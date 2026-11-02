package dev.warpbound.industry.machine;

import dev.warpbound.multiblock.MultiblockCoreBlockEntity;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;

/** Открытая обёртка отдачи через порты и служебное для машин из других пакетов. */
public final class PortPumps {
    private final PortPump pump = new PortPump();

    public void run(ServerLevel level, MultiblockCoreBlockEntity core, MachineSpec spec, PortedMachine machine, long energyBudget) {
        pump.run(level, core, spec, machine, energyBudget);
    }

    /** Порты появились или пропали: провода вокруг должны пересчитать соединения (при освящении соседи не оповещаются). */
    public static void refreshNeighbours(ServerLevel level, MultiblockCoreBlockEntity core) {
        MachineSpec spec = ChainMachines.spec(core.definitionId());
        if (spec == null) return;
        for (ChainMachines.WorldPort p : ChainMachines.worldPorts(core, spec)) {
            BlockPos next = p.pos().relative(p.side());
            BlockState s = level.getBlockState(next);
            if (s.getBlock() instanceof ConduitBlock c) level.setBlock(next, c.connections(level, next), Block.UPDATE_ALL);
        }
    }

    /** Порт одним числом для клиента: x, y, z от ядра, грань, вид, направление. */
    public static long[] pack(MachineSpec spec) {
        long[] out = new long[spec.ports().size()];
        for (int i = 0; i < out.length; i++) {
            MachineSpec.Port p = spec.ports().get(i);
            out[i] = ((long) (p.offset().getX() + 128)) | ((long) p.offset().getY() << 8) | ((long) (p.offset().getZ() + 128) << 16)
                    | ((long) p.face().get3DDataValue() << 24) | ((long) p.kind().ordinal() << 28) | ((p.output() ? 1L : 0L) << 30);
        }
        return out;
    }

    public static BlockPos unpackOffset(long v) {
        return new BlockPos((int) (v & 255) - 128, (int) (v >> 8 & 255), (int) (v >> 16 & 255) - 128);
    }

    public static Direction unpackFace(long v) {
        return Direction.from3DDataValue((int) (v >> 24 & 15));
    }

    public static MachineSpec.Kind unpackKind(long v) {
        return MachineSpec.Kind.values()[(int) (v >> 28 & 3)];
    }

    public static boolean unpackOutput(long v) {
        return (v >> 30 & 1) != 0;
    }
}
