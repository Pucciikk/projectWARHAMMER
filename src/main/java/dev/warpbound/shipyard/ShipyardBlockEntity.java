package dev.warpbound.shipyard;

import dev.warpbound.Warpbound;
import dev.warpbound.core.WarpboundBlockEntities;
import dev.warpbound.core.WarpboundItems;
import dev.warpbound.multiblock.MultiblockCoreBlockEntity;
import dev.warpbound.multiblock.Multiblocks;
import dev.warpbound.network.MultiblockErrorsPayload;
import dev.warpbound.network.ShipyardStatePayload;
import dev.warpbound.quest.QuestManager;
import dev.warpbound.quest.StoryFlags;
import dev.warpbound.ship.Ship;
import dev.warpbound.ship.ShipRegistry;
import dev.warpbound.ship.ShipService;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;

/**
 * Пульт верфи — ядро мультиблока «Стапель». Ведёт постройку корабля по этапам:
 * игрок сдаёт ресурсы, запускает этап, через время в доке появляется очередная часть корпуса.
 * Когда все этапы готовы — старт: синий варп-огонь, док пустеет, корабль становится данными.
 */
public class ShipyardBlockEntity extends MultiblockCoreBlockEntity {
    public static final ResourceLocation MULTIBLOCK = Warpbound.id("shipyard");
    /** В Сезоне 1 верфь строит только фрегат. */
    public static final ResourceLocation DEFAULT_CLASS = Warpbound.id("frigate");
    /** Длительность старта: столько тиков горит варп-огонь, прежде чем док опустеет. */
    private static final int LAUNCH_TICKS = 100;

    private ResourceLocation shipClass = DEFAULT_CLASS;
    /** Сколько этапов уже стоит в доке. */
    private int stage;
    /** Сдано по каждой поставке текущего этапа. */
    private int[] deposited = new int[0];
    /** Тиков до конца работы над этапом; 0 — не строится. */
    private int buildLeft;
    private int launchLeft;
    /** Блоки корабля в доке: их нельзя ломать, при старте они исчезают. */
    private List<BlockPos> shipBlocks = new ArrayList<>();
    /** Кто нажал «Старт»: ему достанется корабль. */
    private UUID launcher;

    public ShipyardBlockEntity(BlockPos pos, BlockState state) {
        super(WarpboundBlockEntities.SHIPYARD, pos, state, MULTIBLOCK);
    }

    public Optional<ShipClass> shipClass() {
        return ShipClasses.REGISTRY.get(shipClass);
    }

    private Optional<ShipClass.Stage> currentStage() {
        return shipClass().filter(c -> stage < c.stages().size()).map(c -> c.stages().get(stage));
    }

    @Override
    public List<BlockPos> protectedPositions() {
        List<BlockPos> all = new ArrayList<>(members());
        all.addAll(shipBlocks);
        return all;
    }

    @Override
    protected boolean canUnform(ServerPlayer player) {
        if (stage == 0 && buildLeft == 0) return true;
        player.displayClientMessage(Component.translatable("shipyard.warpbound.cannot_unform").withStyle(ChatFormatting.RED), true);
        return false;
    }

    @Override
    protected void onFormedBy(ServerPlayer player) {
        QuestManager.setFlag(player, StoryFlags.SHIPYARD_FORMED);
    }

    // ---- действия игрока (приходят пакетом с экрана) ----

    /** Сдать из инвентаря всё, что нужно текущему этапу. */
    public void deposit(ServerPlayer player) {
        var current = currentStage().orElse(null);
        if (current == null || buildLeft > 0) return;
        ensureDepositArray(current);
        var inv = player.getInventory();
        boolean any = false;
        for (int r = 0; r < current.requirements().size(); r++) {
            var req = current.requirements().get(r);
            int need = req.count() - deposited[r];
            for (int i = 0; i < inv.getContainerSize() && need > 0; i++) {
                ItemStack s = inv.getItem(i);
                if (!req.matches(s)) continue;
                int n = Math.min(need, s.getCount());
                s.shrink(n);
                deposited[r] += n;
                need -= n;
                any = true;
            }
        }
        if (any) {
            level.playSound(null, worldPosition, SoundEvents.ARMOR_EQUIP_IRON.value(), SoundSource.BLOCKS, 1f, 0.8f);
            sync();
        }
        sendState(player);
    }

    /** Начать работу над этапом, когда всё сдано. */
    public void startStage(ServerPlayer player) {
        var current = currentStage().orElse(null);
        if (current == null || buildLeft > 0 || !requirementsMet(current)) return;
        if (!(level instanceof ServerLevel server)) return;
        List<BlockPos> blocked = obstructions(server, current);
        if (!blocked.isEmpty()) {
            Warpbound.LOG.debug("Верфь {}: док занят, первый мешающий блок {} = {}", worldPosition, blocked.get(0),
                    server.getBlockState(blocked.get(0)));
            player.displayClientMessage(Component.translatable("shipyard.warpbound.dock_blocked", blocked.size())
                    .withStyle(ChatFormatting.RED), false);
            ServerPlayNetworking.send(player, new MultiblockErrorsPayload(List.of(), blocked));
            return;
        }
        buildLeft = Math.max(1, current.buildSeconds()) * 20;
        level.playSound(null, worldPosition, SoundEvents.BEACON_ACTIVATE, SoundSource.BLOCKS, 1f, 0.7f);
        sync();
        sendState(player);
    }

    /** Старт корабля: все этапы готовы. */
    public void launch(ServerPlayer player) {
        var cls = shipClass().orElse(null);
        if (cls == null || stage < cls.stages().size() || launchLeft > 0) return;
        if (ShipRegistry.get(player.server).ownedBy(player.getUUID()).isPresent()) {
            player.displayClientMessage(Component.translatable("shipyard.warpbound.already_has_ship").withStyle(ChatFormatting.RED), false);
            return;
        }
        launchLeft = LAUNCH_TICKS;
        launcher = player.getUUID();
        sync();
        sendState(player);
    }

    public void sendState(ServerPlayer player) {
        var cls = shipClass().orElse(null);
        List<String> stageNames = cls == null ? List.of() : cls.stages().stream().map(ShipClass.Stage::name).toList();
        var current = currentStage().orElse(null);
        List<String> items = current == null ? List.of() : current.requirements().stream().map(ShipClass.Requirement::item).toList();
        List<Integer> counts = current == null ? List.of() : current.requirements().stream().map(ShipClass.Requirement::count).toList();
        if (current != null) ensureDepositArray(current);
        List<Integer> dep = Arrays.stream(deposited).boxed().toList();
        int total = current == null ? 0 : Math.max(1, current.buildSeconds()) * 20;
        ServerPlayNetworking.send(player, new ShipyardStatePayload(worldPosition, cls == null ? "?" : cls.name(),
                stageNames, stage, items, counts, dep, buildLeft, total, launchLeft > 0));
    }

    // ---- отладка: /wb shipyard ----

    /** Закрыть поставки текущего этапа и закончить его работу почти мгновенно. */
    public boolean debugAdvance(ServerPlayer player) {
        var current = currentStage().orElse(null);
        if (current == null) return false;
        ensureDepositArray(current);
        for (int r = 0; r < deposited.length; r++) deposited[r] = current.requirements().get(r).count();
        if (buildLeft == 0) startStage(player);
        if (buildLeft > 0) buildLeft = 1;
        sync();
        return true;
    }

    public int stage() {
        return stage;
    }

    public List<BlockPos> shipBlocks() {
        return shipBlocks;
    }

    /** Ближайший пульт верфи в загруженных чанках вокруг точки. */
    public static Optional<ShipyardBlockEntity> nearest(ServerLevel level, BlockPos around, int radius) {
        ShipyardBlockEntity best = null;
        double bestDist = Double.MAX_VALUE;
        int r = (radius >> 4) + 1;
        int cx = around.getX() >> 4, cz = around.getZ() >> 4;
        for (int x = cx - r; x <= cx + r; x++) for (int z = cz - r; z <= cz + r; z++) {
            var chunk = level.getChunkSource().getChunkNow(x, z);
            if (chunk == null) continue;
            for (BlockEntity be : chunk.getBlockEntities().values()) {
                if (!(be instanceof ShipyardBlockEntity yard)) continue;
                double d = be.getBlockPos().distSqr(around);
                if (d < bestDist && d <= (double) radius * radius) {
                    bestDist = d;
                    best = yard;
                }
            }
        }
        return Optional.ofNullable(best);
    }

    // ---- работа во времени ----

    @Override
    protected void tickFormed(ServerLevel server) {
        if (buildLeft > 0) {
            buildLeft--;
            if (server.getGameTime() % 10 == 0) workEffects(server);
            if (buildLeft == 0) completeStage(server);
        }
        if (launchLeft > 0) {
            launchLeft--;
            launchEffects(server);
            if (launchLeft == 0) finishLaunch(server);
        }
    }

    private void completeStage(ServerLevel server) {
        var current = currentStage().orElse(null);
        if (current == null) return;
        place(server, current);
        stage++;
        deposited = new int[0];
        server.playSound(null, worldPosition, SoundEvents.ANVIL_LAND, SoundSource.BLOCKS, 1f, 0.6f);
        sync();
    }

    private void place(ServerLevel server, ShipClass.Stage current) {
        Optional<StructureTemplate> template = server.getStructureManager().get(current.structure());
        if (template.isEmpty()) {
            Warpbound.LOG.error("Верфь: нет структуры {}", current.structure());
            return;
        }
        BlockPos origin = orientation().toWorld(worldPosition, current.offset());
        StructurePlaceSettings settings = settings();
        template.get().placeInWorld(server, origin, origin, settings, RandomSource.create(), Block.UPDATE_CLIENTS);
        // Что появилось в габарите этапа — новые блоки корабля
        Set<BlockPos> known = new HashSet<>(shipBlocks);
        List<BlockPos> placed = new ArrayList<>();
        for (BlockPos p : (Iterable<BlockPos>) BlockPos.betweenClosedStream(template.get().getBoundingBox(settings, origin))::iterator) {
            if (!server.getBlockState(p).isAir() && !known.contains(p)) placed.add(p.immutable());
        }
        shipBlocks.addAll(placed);
        Multiblocks.index(server, worldPosition, placed);
    }

    /** Габарит этапа должен быть пуст: в нём могут стоять только уже построенные части корабля. */
    private List<BlockPos> obstructions(ServerLevel server, ShipClass.Stage current) {
        Optional<StructureTemplate> template = server.getStructureManager().get(current.structure());
        if (template.isEmpty()) return List.of();
        BlockPos origin = orientation().toWorld(worldPosition, current.offset());
        Set<BlockPos> known = new HashSet<>(shipBlocks);
        List<BlockPos> blocked = new ArrayList<>();
        for (BlockPos p : (Iterable<BlockPos>) BlockPos.betweenClosedStream(template.get().getBoundingBox(settings(), origin))::iterator) {
            BlockState s = server.getBlockState(p);
            if (!s.isAir() && !s.canBeReplaced() && !known.contains(p)) blocked.add(p.immutable());
        }
        return blocked;
    }

    private StructurePlaceSettings settings() {
        var o = orientation();
        return new StructurePlaceSettings()
                .setRotation(o.rotation())
                .setMirror(o.mirrored() ? Mirror.FRONT_BACK : Mirror.NONE)
                .setIgnoreEntities(true);
    }

    private void finishLaunch(ServerLevel server) {
        Multiblocks.unindex(server, worldPosition, shipBlocks);
        for (BlockPos p : shipBlocks) server.setBlock(p, Blocks.AIR.defaultBlockState(), Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE);
        shipBlocks = new ArrayList<>();
        stage = 0;
        deposited = new int[0];
        server.playSound(null, worldPosition, SoundEvents.END_PORTAL_SPAWN, SoundSource.BLOCKS, 1f, 1.4f);
        ServerPlayer player = launcher == null ? null : server.getServer().getPlayerList().getPlayer(launcher);
        launcher = null;
        if (player != null) {
            Ship ship = ShipService.createFor(player, Component.translatable("shipyard.warpbound.default_ship_name").getString());
            player.displayClientMessage(Component.translatable("shipyard.warpbound.launched", ship.name)
                    .withStyle(ChatFormatting.AQUA), false);
            QuestManager.setFlag(player, StoryFlags.SHIP_LAUNCHED);
            // Маяк, чтобы подняться на борт с планеты
            ItemStack homer = new ItemStack(WarpboundItems.TELEPORT_HOMER);
            if (!player.getInventory().add(homer)) player.drop(homer, false);
        }
        sync();
    }

    private void workEffects(ServerLevel server) {
        RandomSource r = server.random;
        BlockPos p = shipBlocks.isEmpty() ? worldPosition : shipBlocks.get(r.nextInt(shipBlocks.size()));
        server.sendParticles(ParticleTypes.ELECTRIC_SPARK, p.getX() + r.nextDouble(), p.getY() + 1, p.getZ() + r.nextDouble(),
                6, 0.3, 0.3, 0.3, 0.1);
        if (r.nextInt(4) == 0) server.playSound(null, p, SoundEvents.ANVIL_USE, SoundSource.BLOCKS, 0.5f, 1.2f + r.nextFloat() * 0.3f);
    }

    private void launchEffects(ServerLevel server) {
        RandomSource r = server.random;
        for (int i = 0; i < 12 && !shipBlocks.isEmpty(); i++) {
            BlockPos p = shipBlocks.get(r.nextInt(shipBlocks.size()));
            server.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, p.getX() + 0.5, p.getY() + 0.5, p.getZ() + 0.5, 3, 0.4, 0.4, 0.4, 0.02);
        }
        if (launchLeft % 20 == 0) server.playSound(null, worldPosition, SoundEvents.FIRECHARGE_USE, SoundSource.BLOCKS, 1.5f, 0.5f);
    }

    private boolean requirementsMet(ShipClass.Stage current) {
        ensureDepositArray(current);
        for (int r = 0; r < current.requirements().size(); r++) {
            if (deposited[r] < current.requirements().get(r).count()) return false;
        }
        return true;
    }

    private void ensureDepositArray(ShipClass.Stage current) {
        if (deposited.length != current.requirements().size()) deposited = Arrays.copyOf(deposited, current.requirements().size());
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.putString("shipClass", shipClass.toString());
        tag.putInt("stage", stage);
        tag.putIntArray("deposited", deposited);
        tag.putInt("buildLeft", buildLeft);
        tag.putInt("launchLeft", launchLeft);
        if (launcher != null) tag.putUUID("launcher", launcher);
        tag.putLongArray("shipBlocks", shipBlocks.stream().mapToLong(BlockPos::asLong).toArray());
    }

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        if (tag.contains("shipClass")) shipClass = ResourceLocation.parse(tag.getString("shipClass"));
        stage = tag.getInt("stage");
        deposited = tag.getIntArray("deposited");
        buildLeft = tag.getInt("buildLeft");
        launchLeft = tag.getInt("launchLeft");
        launcher = tag.hasUUID("launcher") ? tag.getUUID("launcher") : null;
        shipBlocks = new ArrayList<>();
        for (long l : tag.getLongArray("shipBlocks")) shipBlocks.add(BlockPos.of(l));
    }
}
