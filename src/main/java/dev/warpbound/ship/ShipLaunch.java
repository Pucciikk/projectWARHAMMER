package dev.warpbound.ship;

import dev.warpbound.Warpbound;
import dev.warpbound.core.WarpboundBlocks;
import dev.warpbound.ship.block.BoardingHatchBlock;
import dev.warpbound.ship.block.BulkheadDoorBlock;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Vec3i;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * Выход корабля со стапеля в космос: постройка целиком (корпус и отсеки) переносится в пространство
 * над миром (измерение warpbound:ship_interior, участок корабля), вместе со всеми, кто на борту.
 * Нос всегда смотрит на +Z — так рисуется небо и движение звёзд.
 */
public final class ShipLaunch {
    /** Высота нижней точки корабля в космосе. */
    private static final int SPACE_FLOOR_Y = 40;

    private ShipLaunch() {
    }

    /** Задраить люки: внешние — закрыть и запереть, внутренние гермодвери — закрыть. */
    public static void sealHatches(ServerLevel level, List<BlockPos> blocks) {
        for (BlockPos p : blocks) {
            BlockState s = level.getBlockState(p);
            if (s.getBlock() instanceof BulkheadDoorBlock) {
                boolean hatch = s.getBlock() instanceof BoardingHatchBlock;
                level.setBlock(p, s.setValue(BulkheadDoorBlock.OPEN, false).setValue(BulkheadDoorBlock.LOCKED, hatch), Block.UPDATE_ALL);
            }
        }
    }

    /**
     * Перенести корабль. blocks — все блоки корабля в доке, rotation — как он стоит в доке (поворот пульта верфи).
     * Возвращает созданный корабль; блоки в доке убирает вызывающий.
     */
    public static Ship toSpace(ServerLevel dock, List<BlockPos> blocks, Rotation rotation, UUID owner, String name) {
        var server = dock.getServer();
        ServerLevel space = ShipInteriors.level(server);
        if (space == null || blocks.isEmpty()) return null;
        BoundingBox box = BoundingBox.encapsulatingPositions(blocks).orElseThrow();
        BlockPos min = new BlockPos(box.minX(), box.minY(), box.minZ());
        Vec3i size = new Vec3i(box.getXSpan(), box.getYSpan(), box.getZSpan());

        StructureTemplate template = new StructureTemplate();
        template.fillFromWorld(dock, min, size, false, Blocks.STRUCTURE_VOID);

        // кто на борту — с запасом в блок вокруг корпуса
        AABB aabb = new AABB(Vec3.atLowerCornerOf(min), Vec3.atLowerCornerOf(min.offset(size))).inflate(1);
        List<ServerPlayer> crew = dock.getEntitiesOfClass(ServerPlayer.class, aabb);

        Ship ship = ShipRegistry.get(server).create(owner, name);
        // в доке корабль повёрнут как пульт верфи; в космосе — нос на +Z
        Rotation back = inverse(rotation);
        StructurePlaceSettings settings = new StructurePlaceSettings().setRotation(back).setMirror(Mirror.NONE).setIgnoreEntities(true);
        BlockPos origin = ShipInteriors.origin(ship.plot);
        BoundingBox placedBox = template.getBoundingBox(settings, BlockPos.ZERO);
        BlockPos at = new BlockPos(origin.getX() - (placedBox.minX() + placedBox.maxX()) / 2, SPACE_FLOOR_Y - placedBox.minY(),
                origin.getZ() - (placedBox.minZ() + placedBox.maxZ()) / 2);
        template.placeInWorld(space, at, at, settings, RandomSource.create(), Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE);
        BoundingBox spaceBox = template.getBoundingBox(settings, at);

        // точки на борту: мостик (у пульта), реактор, иллюминаторы под бронеставни
        scan(space, spaceBox, ship, origin);

        for (ServerPlayer p : crew) {
            Vec3 rel = p.position().subtract(Vec3.atLowerCornerOf(min));
            Vec3 moved = StructureTemplate.transform(rel, Mirror.NONE, back, BlockPos.ZERO).add(Vec3.atLowerCornerOf(at));
            float yaw = p.getYRot() + switch (back) {
                case CLOCKWISE_90 -> 90f;
                case CLOCKWISE_180 -> 180f;
                case COUNTERCLOCKWISE_90 -> -90f;
                default -> 0f;
            };
            p.teleportTo(space, moved.x, moved.y, moved.z, yaw, p.getXRot());
        }
        ShipRegistry.get(server).setDirty();
        Warpbound.LOG.info("Корабль «{}» вышел в космос: участок {}, блоков {}", name, ship.plot, blocks.size());
        return ship;
    }

    private static void scan(ServerLevel space, BoundingBox box, Ship ship, BlockPos origin) {
        List<Long> shutters = new ArrayList<>();
        List<Integer> states = new ArrayList<>();
        BlockPos console = null;
        for (BlockPos p : BlockPos.betweenClosed(box.minX(), box.minY(), box.minZ(), box.maxX(), box.maxY(), box.maxZ())) {
            BlockState s = space.getBlockState(p);
            if (s.is(WarpboundBlocks.COMMAND_CONSOLE)) {
                console = p.immutable();
                // мостик: пульт смотрит на трон, вошедших ставим между ними, на помост
                ship.spawnRel = p.offset(0, 0, -1).subtract(origin);
            } else if (s.is(WarpboundBlocks.REACTOR_CORE)) {
                ship.reactorRel = p.immutable().subtract(origin);
            }
        }
        for (BlockPos p : BlockPos.betweenClosed(box.minX(), box.minY(), box.minZ(), box.maxX(), box.maxY(), box.maxZ())) {
            BlockState s = space.getBlockState(p);
            if (!(s.is(Blocks.TINTED_GLASS) || s.is(Blocks.ORANGE_STAINED_GLASS) || s.is(Blocks.GLASS))) continue;
            if (onBridge(console, p)) continue;   // окна мостика не закрываются: капитан смотрит в варп
            shutters.add(p.asLong());
            states.add(Block.getId(s));
        }
        ship.shutterPos = shutters.stream().mapToLong(Long::longValue).toArray();
        ship.shutterStates = states.stream().mapToInt(Integer::intValue).toArray();
    }

    /** Купол мостика: от пульта капитана до носовых окон (нос в космосе всегда на +Z). */
    private static boolean onBridge(BlockPos console, BlockPos p) {
        if (console == null) return false;
        int dx = p.getX() - console.getX(), dy = p.getY() - console.getY(), dz = p.getZ() - console.getZ();
        return Math.abs(dx) <= 12 && dy >= -6 && dy <= 20 && dz >= -10 && dz <= 28;
    }

    private static Rotation inverse(Rotation r) {
        return switch (r) {
            case CLOCKWISE_90 -> Rotation.COUNTERCLOCKWISE_90;
            case COUNTERCLOCKWISE_90 -> Rotation.CLOCKWISE_90;
            default -> r;
        };
    }

    /** Закрыть или открыть бронеставни на всех иллюминаторах (скрежет — у ShipFlight). */
    public static void setShutters(ServerLevel space, Ship ship, boolean closed) {
        BlockState plate = WarpboundBlocks.HULL_PLATING.defaultBlockState();
        for (int i = 0; i < ship.shutterPos.length; i++) {
            BlockPos p = BlockPos.of(ship.shutterPos[i]);
            space.setBlock(p, closed ? plate : Block.stateById(ship.shutterStates[i]), Block.UPDATE_ALL);
        }
    }

    /** Для отладки: расположение блоков-меток корабля. */
    public static Map<String, BlockPos> marks(Ship ship) {
        BlockPos o = ShipInteriors.origin(ship.plot);
        return Map.of("spawn", ship.spawnRel == null ? o : o.offset(ship.spawnRel),
                "reactor", ship.reactorRel == null ? o : o.offset(ship.reactorRel));
    }
}
