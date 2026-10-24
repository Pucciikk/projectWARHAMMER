package dev.warpbound.multiblock;

import dev.warpbound.network.MultiblockErrorsPayload;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Ядро мультиблока: помнит, собрана ли машина, как она повёрнута и из каких блоков состоит.
 * Конкретные машины наследуют его и добавляют свою работу в {@link #tickFormed}.
 */
public class MultiblockCoreBlockEntity extends BlockEntity {
    /** Как часто собранная машина перепроверяет себя (взрывы, поршни). */
    private static final int RECHECK_TICKS = 200;
    /** Сколько разных недостающих блоков перечислять в сообщении. */
    private static final int REPORT_LINES = 3;

    private final ResourceLocation definitionId;
    private boolean formed;
    private MultiblockOrientation orientation = new MultiblockOrientation(net.minecraft.core.Direction.NORTH, false);
    private List<BlockPos> members = List.of();

    public MultiblockCoreBlockEntity(BlockEntityType<?> type, BlockPos pos, BlockState state, ResourceLocation definitionId) {
        super(type, pos, state);
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

    /** Освящение ключом: проверить шаблон, собрать машину или показать ошибки. */
    public void tryForm(ServerPlayer player) {
        if (!(level instanceof ServerLevel server)) return;
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
        var facing = getBlockState().getValue(HorizontalDirectionalBlock.FACING);
        var result = MultiblockMatcher.best(server, worldPosition, def, Multiblocks.cells(definitionId), facing);
        if (!result.ok()) {
            report(player, result);
            return;
        }
        form(server, result);
        onFormedBy(player);
        player.displayClientMessage(Component.translatable("multiblock.warpbound.formed", Component.translatable(def.name()))
                .withStyle(ChatFormatting.GREEN), true);
    }

    private void form(ServerLevel server, MultiblockMatcher.Result result) {
        formed = true;
        orientation = result.orientation();
        members = List.copyOf(result.members());
        Multiblocks.index(server, worldPosition, protectedPositions());
        sync();
        // Освящение: искры по всей машине, пар у ядра
        for (int i = 0; i < members.size(); i += Math.max(1, members.size() / 40)) {
            BlockPos p = members.get(i);
            server.sendParticles(ParticleTypes.ELECTRIC_SPARK, p.getX() + 0.5, p.getY() + 1, p.getZ() + 0.5, 4, 0.3, 0.2, 0.3, 0.05);
        }
        server.sendParticles(ParticleTypes.CLOUD, worldPosition.getX() + 0.5, worldPosition.getY() + 1, worldPosition.getZ() + 0.5,
                12, 0.4, 0.3, 0.4, 0.02);
        server.playSound(null, worldPosition, SoundEvents.ANVIL_USE, SoundSource.BLOCKS, 0.8f, 0.7f);
        server.playSound(null, worldPosition, SoundEvents.BEACON_POWER_SELECT, SoundSource.BLOCKS, 1f, 0.6f);
        onFormed(server);
    }

    /** Разбор ключом: машина снова становится грудой блоков, ничего не теряется. */
    public void unform(ServerPlayer player) {
        if (!formed || !(level instanceof ServerLevel server)) return;
        if (player != null && !canUnform(player)) return;
        disband(server);
        if (player != null) {
            player.displayClientMessage(Component.translatable("multiblock.warpbound.unformed").withStyle(ChatFormatting.GRAY), true);
        }
    }

    private void disband(ServerLevel server) {
        Multiblocks.unindex(server, worldPosition, protectedPositions());
        formed = false;
        members = List.of();
        sync();
        server.playSound(null, worldPosition, SoundEvents.IRON_DOOR_CLOSE, SoundSource.BLOCKS, 1f, 0.6f);
        onUnformed(server);
    }

    public static void serverTick(Level level, BlockPos pos, BlockState state, MultiblockCoreBlockEntity be) {
        if (!be.formed || !(level instanceof ServerLevel server)) return;
        if (server.getGameTime() % RECHECK_TICKS == 0 && !be.stillIntact(server)) {
            be.disband(server);
            return;
        }
        be.tickFormed(server);
    }

    private boolean stillIntact(ServerLevel server) {
        if (Multiblocks.definition(definitionId).isEmpty()) return false;
        return MultiblockMatcher.match(server, worldPosition, Multiblocks.cells(definitionId), orientation).ok();
    }

    /** Ядро сломано (например, в креативе) — убрать машину из индекса. */
    public void onCoreRemoved() {
        if (formed && level instanceof ServerLevel server) disband(server);
    }

    /** Всё, что нельзя ломать, пока машина собрана: её блоки и то, что она построила. */
    public List<BlockPos> protectedPositions() {
        return members;
    }

    /** Можно ли сейчас разобрать машину ключом; при отказе машина сама объясняет игроку почему. */
    protected boolean canUnform(ServerPlayer player) {
        return true;
    }

    /** Кто освятил машину — например, чтобы засчитать квест. */
    protected void onFormedBy(ServerPlayer player) {
    }

    protected void onFormed(ServerLevel level) {
    }

    protected void onUnformed(ServerLevel level) {
    }

    protected void tickFormed(ServerLevel level) {
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

    protected void sync() {
        setChanged();
        if (level != null) level.sendBlockUpdated(worldPosition, getBlockState(), getBlockState(), 3);
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.putBoolean("formed", formed);
        tag.putInt("orientation", orientation.pack());
        tag.putLongArray("members", members.stream().mapToLong(BlockPos::asLong).toArray());
    }

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        formed = tag.getBoolean("formed");
        orientation = MultiblockOrientation.unpack(tag.getInt("orientation"));
        long[] packed = tag.getLongArray("members");
        List<BlockPos> list = new ArrayList<>(packed.length);
        for (long l : packed) list.add(BlockPos.of(l));
        members = List.copyOf(list);
    }

    @Override
    public CompoundTag getUpdateTag(HolderLookup.Provider registries) {
        // Клиенту нужны только флаг и ориентация, список блоков ему не нужен
        CompoundTag tag = new CompoundTag();
        tag.putBoolean("formed", formed);
        tag.putInt("orientation", orientation.pack());
        return tag;
    }

    @Override
    public Packet<ClientGamePacketListener> getUpdatePacket() {
        return ClientboundBlockEntityDataPacket.create(this);
    }
}
