package dev.warpbound.multiblock;

import dev.warpbound.network.MultiblockErrorsPayload;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Состояние мультиблока при ядре: собран ли, как повёрнут, из каких блоков.
 * Сборка (освящение), разбор, перепроверка целостности, ошибки с подсветкой.
 * <p>
 * Если машина прячет груду ({@link MultiblockHost#hidesMembers()}), при сборке её блоки заменяются
 * невидимыми «частями машины», которые помнят исходный блок; при разборе всё возвращается как было.
 */
public final class MultiblockController {
    /** Как часто собранная машина перепроверяет себя (взрывы, поршни). */
    private static final int RECHECK_TICKS = 200;
    /** Сколько разных недостающих блоков перечислять в сообщении. */
    private static final int REPORT_LINES = 3;

    private final BlockEntity owner;
    private final MultiblockHost host;
    private final ResourceLocation definitionId;
    private boolean formed;
    private MultiblockOrientation orientation = new MultiblockOrientation(Direction.NORTH, false);
    private List<BlockPos> members = List.of();

    public MultiblockController(BlockEntity owner, ResourceLocation definitionId) {
        this.owner = owner;
        this.host = (MultiblockHost) owner;
        this.definitionId = definitionId;
    }

    public boolean isFormed() {
        return formed;
    }

    public MultiblockOrientation orientation() {
        return orientation;
    }

    public List<BlockPos> members() {
        return members;
    }

    public ResourceLocation definitionId() {
        return definitionId;
    }

    private BlockPos pos() {
        return owner.getBlockPos();
    }

    /** Освящение: проверить шаблон, собрать машину или показать ошибки. */
    public void tryForm(ServerPlayer player) {
        if (!(owner.getLevel() instanceof ServerLevel server)) return;
        if (formed) {
            player.displayClientMessage(Component.translatable("multiblock.warpbound.already_formed")
                    .withStyle(ChatFormatting.GRAY), true);
            return;
        }
        var def = Multiblocks.definition(definitionId).orElse(null);
        if (def == null) {
            player.displayClientMessage(Component.literal("Нет шаблона " + definitionId).withStyle(ChatFormatting.RED), false);
            return;
        }
        Direction facing = owner.getBlockState().getValue(HorizontalDirectionalBlock.FACING);
        var result = MultiblockMatcher.best(server, pos(), def, Multiblocks.cells(definitionId), facing);
        if (!result.ok()) {
            report(player, result);
            return;
        }
        form(server, result);
        host.onFormedBy(player);
        player.displayClientMessage(Component.translatable("multiblock.warpbound.formed", Component.translatable(def.name()))
                .withStyle(ChatFormatting.GREEN), true);
    }

    private void form(ServerLevel server, MultiblockMatcher.Result result) {
        formed = true;
        orientation = result.orientation();
        members = List.copyOf(result.members());
        if (host.hidesMembers()) {
            for (BlockPos p : members) MachinePartBlock.replace(server, p, pos());
        }
        setCoreFormed(server, true);
        Multiblocks.index(server, pos(), host.protectedPositions());
        sync();
        // Освящение: искры по всей машине, пар у ядра
        for (int i = 0; i < members.size(); i += Math.max(1, members.size() / 40)) {
            BlockPos p = members.get(i);
            server.sendParticles(ParticleTypes.ELECTRIC_SPARK, p.getX() + 0.5, p.getY() + 1, p.getZ() + 0.5, 4, 0.3, 0.2, 0.3, 0.05);
        }
        BlockPos c = pos();
        server.sendParticles(ParticleTypes.CLOUD, c.getX() + 0.5, c.getY() + 1, c.getZ() + 0.5, 12, 0.4, 0.3, 0.4, 0.02);
        server.playSound(null, c, SoundEvents.ANVIL_USE, SoundSource.BLOCKS, 0.8f, 0.7f);
        server.playSound(null, c, SoundEvents.BEACON_POWER_SELECT, SoundSource.BLOCKS, 1f, 0.6f);
        host.onFormed(server);
    }

    /** Разбор ключом: машина снова становится грудой блоков, ничего не теряется. */
    public void unform(ServerPlayer player) {
        if (!formed || !(owner.getLevel() instanceof ServerLevel server)) return;
        if (player != null && !host.canUnform(player)) return;
        disband(server);
        if (player != null) {
            player.displayClientMessage(Component.translatable("multiblock.warpbound.unformed").withStyle(ChatFormatting.GRAY), true);
        }
    }

    private void disband(ServerLevel server) {
        Multiblocks.unindex(server, pos(), host.protectedPositions());
        if (host.hidesMembers()) {
            for (BlockPos p : members) MachinePartBlock.restore(server, p, pos());
        }
        formed = false;
        members = List.of();
        setCoreFormed(server, false);
        sync();
        server.playSound(null, pos(), SoundEvents.IRON_DOOR_CLOSE, SoundSource.BLOCKS, 1f, 0.6f);
        host.onUnformed(server);
    }

    private void setCoreFormed(Level level, boolean value) {
        BlockState state = level.getBlockState(pos());
        if (state.hasProperty(MultiblockHost.FORMED) && state.getValue(MultiblockHost.FORMED) != value) {
            level.setBlock(pos(), state.setValue(MultiblockHost.FORMED, value), Block.UPDATE_ALL);
        }
    }

    /** Вызывать из тикера ядра на сервере. */
    public void serverTick(ServerLevel server) {
        if (!formed) return;
        if (server.getGameTime() % RECHECK_TICKS == 0 && !stillIntact(server)) {
            disband(server);
            return;
        }
        host.tickFormed(server);
    }

    private boolean stillIntact(ServerLevel server) {
        if (Multiblocks.definition(definitionId).isEmpty()) return false;
        if (host.hidesMembers()) {
            // груда спрятана: целы ли все части и помнят ли они это ядро
            for (BlockPos p : members) {
                if (!(server.getBlockEntity(p) instanceof MachinePartBlockEntity part) || !pos().equals(part.core())) return false;
            }
            return true;
        }
        return MultiblockMatcher.match(server, pos(), Multiblocks.cells(definitionId), orientation).ok();
    }

    /** Ядро сломано (например, в креативе) — вернуть груду и убрать машину из индекса. */
    public void onCoreRemoved() {
        if (formed && owner.getLevel() instanceof ServerLevel server) disband(server);
    }

    /** Часть машины сломана (креатив, команда) — машина разваливается, остальное возвращается грудой. */
    public void onPartRemoved(BlockPos part) {
        if (!formed || !(owner.getLevel() instanceof ServerLevel server)) return;
        members = members.stream().filter(p -> !p.equals(part)).toList();
        disband(server);
    }

    private void report(ServerPlayer player, MultiblockMatcher.Result result) {
        Map<String, Integer> missing = new LinkedHashMap<>();
        Map<String, Component> names = new LinkedHashMap<>();
        List<BlockPos> wrongPos = new ArrayList<>();
        List<BlockPos> missingPos = new ArrayList<>();
        for (var m : result.mismatches()) {
            String key = m.expected().getString();
            missing.merge(key, 1, Integer::sum);
            names.putIfAbsent(key, m.expected());
            if (m.actual().isAir()) {
                missingPos.add(m.pos());
            } else {
                wrongPos.add(m.pos());
            }
        }
        player.displayClientMessage(Component.translatable("multiblock.warpbound.not_formed", result.mismatches().size())
                .withStyle(ChatFormatting.RED), false);
        int lines = 0;
        for (var e : missing.entrySet()) {
            if (lines++ >= REPORT_LINES) break;
            player.displayClientMessage(Component.literal(" • ").append(names.get(e.getKey())).append(" ×" + e.getValue())
                    .withStyle(ChatFormatting.GOLD), false);
        }
        if (!wrongPos.isEmpty()) {
            player.displayClientMessage(Component.translatable("multiblock.warpbound.wrong_blocks", wrongPos.size())
                    .withStyle(ChatFormatting.RED), false);
        }
        ServerPlayNetworking.send(player, new MultiblockErrorsPayload(missingPos, wrongPos));
    }

    public void sync() {
        owner.setChanged();
        Level level = owner.getLevel();
        if (level != null) level.sendBlockUpdated(pos(), owner.getBlockState(), owner.getBlockState(), Block.UPDATE_ALL);
    }

    public void save(CompoundTag tag) {
        tag.putBoolean("formed", formed);
        tag.putInt("orientation", orientation.pack());
        tag.putLongArray("members", members.stream().mapToLong(BlockPos::asLong).toArray());
    }

    public void load(CompoundTag tag) {
        formed = tag.getBoolean("formed");
        orientation = MultiblockOrientation.unpack(tag.getInt("orientation"));
        if (tag.contains("members")) {
            long[] packed = tag.getLongArray("members");
            List<BlockPos> list = new ArrayList<>(packed.length);
            for (long l : packed) list.add(BlockPos.of(l));
            members = List.copyOf(list);
        }
    }

    /** Клиенту нужны только флаг и ориентация, список блоков ему не нужен. */
    public void writeUpdateTag(CompoundTag tag) {
        tag.putBoolean("formed", formed);
        tag.putInt("orientation", orientation.pack());
    }
}
