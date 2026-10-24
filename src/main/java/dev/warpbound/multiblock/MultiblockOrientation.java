package dev.warpbound.multiblock;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.block.Rotation;

/**
 * Как шаблон лежит в мире: куда смотрит перед машины и отражён ли он.
 * Шаблон описан для ядра, смотрящего на север; поворот — вокруг ядра.
 */
public record MultiblockOrientation(Direction facing, boolean mirrored) {
    public BlockPos toWorld(BlockPos core, BlockPos offset) {
        BlockPos local = mirrored ? new BlockPos(-offset.getX(), offset.getY(), offset.getZ()) : offset;
        return core.offset(local.rotate(rotation()));
    }

    public Rotation rotation() {
        return switch (facing) {
            case EAST -> Rotation.CLOCKWISE_90;
            case SOUTH -> Rotation.CLOCKWISE_180;
            case WEST -> Rotation.COUNTERCLOCKWISE_90;
            default -> Rotation.NONE;
        };
    }

    public int pack() {
        return facing.get2DDataValue() | (mirrored ? 4 : 0);
    }

    public static MultiblockOrientation unpack(int packed) {
        return new MultiblockOrientation(Direction.from2DDataValue(packed & 3), (packed & 4) != 0);
    }
}
