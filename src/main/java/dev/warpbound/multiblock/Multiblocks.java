package dev.warpbound.multiblock;

import dev.warpbound.core.DataRegistry;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerBlockEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.player.PlayerBlockBreakEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.Level;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * Реестр шаблонов мультиблоков и индекс «блок → ядро» собранных машин.
 * Индекс живёт в памяти: ядра заносят себя при загрузке чанка и при сборке.
 */
public final class Multiblocks {
    public static final DataRegistry<MultiblockDefinition> REGISTRY = new DataRegistry<>("multiblock", MultiblockDefinition.CODEC);

    private static final Map<ResourceLocation, List<MultiblockDefinition.Cell>> CELLS = new HashMap<>();
    private static final Map<ResourceKey<Level>, Map<BlockPos, BlockPos>> MEMBERS = new HashMap<>();

    private Multiblocks() {
    }

    public static void register() {
        REGISTRY.onReload(reg -> CELLS.clear());
        ServerLifecycleEvents.SERVER_STOPPED.register(server -> MEMBERS.clear());

        ServerBlockEntityEvents.BLOCK_ENTITY_LOAD.register((be, level) -> {
            if (be instanceof MultiblockHost core && core.isFormed()) index(level, be.getBlockPos(), core.protectedPositions());
        });
        ServerBlockEntityEvents.BLOCK_ENTITY_UNLOAD.register((be, level) -> {
            if (be instanceof MultiblockHost core) unindex(level, be.getBlockPos(), core.protectedPositions());
        });

        // Собранную машину не разобрать киркой: только ключом
        PlayerBlockBreakEvents.BEFORE.register((level, player, pos, state, be) -> {
            if (player.isCreative() && player.isShiftKeyDown()) return true;
            boolean protectedPart = coreOf(level, pos).isPresent()
                    || be instanceof MultiblockHost core && core.isFormed();
            if (!protectedPart) return true;
            player.displayClientMessage(Component.translatable("multiblock.warpbound.use_key")
                    .withStyle(ChatFormatting.GOLD), true);
            return false;
        });
    }

    public static Optional<MultiblockDefinition> definition(ResourceLocation id) {
        return REGISTRY.get(id);
    }

    /** Клетки шаблона, разобранные один раз на загрузку датапака. */
    public static List<MultiblockDefinition.Cell> cells(ResourceLocation id) {
        return CELLS.computeIfAbsent(id, key -> REGISTRY.get(key).map(MultiblockDefinition::cells).orElse(List.of()));
    }

    /**
     * Поставить все блоки шаблона вокруг ядра (ядро не трогается). Для отладки и тестов;
     * позже на этом же построен сервитор-строитель.
     */
    public static int placeAll(Level level, BlockPos core, ResourceLocation id, MultiblockOrientation orientation) {
        int placed = 0;
        for (MultiblockDefinition.Cell cell : cells(id)) {
            BlockPos pos = orientation.toWorld(core, cell.offset());
            if (cell.matches().test(level.getBlockState(pos))) continue;
            level.setBlockAndUpdate(pos, cell.place());
            placed++;
        }
        return placed;
    }

    public static Optional<BlockPos> coreOf(Level level, BlockPos member) {
        Map<BlockPos, BlockPos> map = MEMBERS.get(level.dimension());
        return map == null ? Optional.empty() : Optional.ofNullable(map.get(member));
    }

    public static void index(Level level, BlockPos core, List<BlockPos> members) {
        Map<BlockPos, BlockPos> map = MEMBERS.computeIfAbsent(level.dimension(), k -> new HashMap<>());
        for (BlockPos m : members) map.put(m.immutable(), core.immutable());
    }

    public static void unindex(Level level, BlockPos core, List<BlockPos> members) {
        Map<BlockPos, BlockPos> map = MEMBERS.get(level.dimension());
        if (map == null) return;
        for (BlockPos m : members) map.remove(m, core);
    }
}
