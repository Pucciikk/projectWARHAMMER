package dev.warpbound.ship;

import dev.warpbound.Warpbound;
import dev.warpbound.config.WarpboundConfig;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.Level;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.LecternBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;

/**
 * Измерение интерьеров. Каждому кораблю — свой участок вдоль оси X с шагом plotSpacing.
 * Нос корабля смотрит на +Z: туда же направлен «туннель» неба варпа.
 */
public final class ShipInteriors {
    public static final ResourceKey<Level> LEVEL_KEY = ResourceKey.create(Registries.DIMENSION, Warpbound.id("ship_interior"));

    /** Пол корабля на этой высоте. */
    public static final int DECK_Y = 64;

    // Габариты временного корпуса v0 (внутренняя часть)
    private static final int HALF_WIDTH = 6;
    private static final int HEIGHT = 7;
    private static final int HALF_LENGTH = 15;

    private ShipInteriors() {
    }

    public static ServerLevel level(MinecraftServer server) {
        return server.getLevel(LEVEL_KEY);
    }

    public static boolean isInterior(Level level) {
        return level.dimension().equals(LEVEL_KEY);
    }

    public static BlockPos origin(int plot) {
        return new BlockPos(plot * WarpboundConfig.get().plotSpacing, DECK_Y, 0);
    }

    /** Номер участка по координате X. Участок 0 не используется. */
    public static int plotAt(double x) {
        return (int) Math.round(x / WarpboundConfig.get().plotSpacing);
    }

    /** Точка появления на борту, лицом к носу: из раскладки, а у старых кораблей v0 — на корме. */
    public static BlockPos spawn(Ship ship) {
        if (ship.layout != null) {
            var layout = ShipLayout.REGISTRY.get(ship.layout);
            if (layout.isPresent()) return origin(ship.plot).offset(layout.get().spawn());
        }
        return origin(ship.plot).offset(0, 1, -HALF_LENGTH + 3);
    }

    /**
     * Интерьер из отсеков-шаблонов по раскладке. Возвращает false, если раскладки или отсека нет:
     * тогда корабль получает временный корпус v0, чтобы игрок не провалился в пустоту.
     */
    public static boolean buildFromLayout(ServerLevel level, int plot, ResourceLocation layoutId) {
        return buildFromLayout(level, origin(plot), layoutId);
    }

    /** То же, но от произвольной точки палубы — для тестов и будущей перестройки отсеков. */
    public static boolean buildFromLayout(ServerLevel level, BlockPos o, ResourceLocation layoutId) {
        var layout = ShipLayout.REGISTRY.get(layoutId).orElse(null);
        if (layout == null) return false;
        var manager = level.getStructureManager();
        StructurePlaceSettings settings = new StructurePlaceSettings().setIgnoreEntities(true);
        for (var compartment : layout.compartments()) {
            var template = manager.get(compartment.structure());
            if (template.isEmpty()) {
                Warpbound.LOG.error("Корабль: нет отсека {}", compartment.structure());
                return false;
            }
            BlockPos at = o.offset(compartment.offset());
            template.get().placeInWorld(level, at, at, settings, level.random, Block.UPDATE_CLIENTS);
        }
        return true;
    }

    /**
     * Временный корпус v0: коридор-мостик с панорамным окном в носу и иллюминаторами по бортам.
     * Позже его заменит генерация из шаблонов корпуса и модулей.
     */
    public static void buildPlaceholderHull(ServerLevel level, int plot) {
        BlockPos o = origin(plot);
        BlockState floor = Blocks.POLISHED_DEEPSLATE.defaultBlockState();
        BlockState wall = Blocks.DEEPSLATE_TILES.defaultBlockState();
        BlockState ceiling = Blocks.DEEPSLATE_BRICKS.defaultBlockState();
        BlockState rib = Blocks.POLISHED_BLACKSTONE_BRICKS.defaultBlockState();
        BlockState glass = Blocks.GLASS.defaultBlockState();
        BlockState light = Blocks.SEA_LANTERN.defaultBlockState();
        BlockState air = Blocks.AIR.defaultBlockState();

        int w = HALF_WIDTH + 1, l = HALF_LENGTH + 1, h = HEIGHT + 1;
        for (int x = -w; x <= w; x++) {
            for (int y = 0; y <= h; y++) {
                for (int z = -l; z <= l; z++) {
                    boolean shell = Math.abs(x) == w || y == 0 || y == h || Math.abs(z) == l;
                    BlockState state;
                    if (!shell) {
                        state = air;
                    } else if (y == 0) {
                        state = floor;
                    } else if (y == h) {
                        state = (x == 0 && z % 4 == 0) ? light : ceiling;
                    } else if (z == l && Math.abs(x) <= 4 && y >= 2 && y <= 6) {
                        state = glass; // панорамное окно мостика
                    } else if (Math.abs(x) == w && z % 6 == 0 && Math.abs(z) < l && (y == 3 || y == 4)) {
                        state = glass; // бортовые иллюминаторы
                    } else if (Math.abs(x) == w && Math.abs(z) % 6 == 3) {
                        state = rib; // шпангоуты
                    } else {
                        state = wall;
                    }
                    level.setBlock(o.offset(x, y, z), state, 3);
                }
            }
        }
        // Навигационный стол мостика (пока просто кафедра)
        level.setBlock(o.offset(0, 1, l - 3),
                Blocks.LECTERN.defaultBlockState().setValue(LecternBlock.FACING, Direction.NORTH), 3);
    }
}
