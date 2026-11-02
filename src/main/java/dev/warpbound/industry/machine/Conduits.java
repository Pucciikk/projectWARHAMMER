package dev.warpbound.industry.machine;

import net.fabricmc.fabric.api.transfer.v1.fluid.FluidStorage;
import net.fabricmc.fabric.api.transfer.v1.fluid.FluidVariant;
import net.fabricmc.fabric.api.transfer.v1.item.ItemStorage;
import net.fabricmc.fabric.api.transfer.v1.storage.Storage;
import net.fabricmc.fabric.api.transfer.v1.storage.StorageUtil;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import team.reborn.energy.api.EnergyStorage;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.WeakHashMap;

/**
 * Обход сети проводов: от порта по трубам до всех, кто может принять. Сеть считается при изменении и держится в кэше у машины,
 * а передача идёт раз в {@link #PERIOD} тиков только от тех машин, которым есть что отдать. Так трубы не тикают и не нагружают сервер.
 */
public final class Conduits {
    public static final int PERIOD = 10;
    private static final int MAX_NODES = 2048;
    private static final Map<Level, long[]> GENERATION = new WeakHashMap<>();

    private Conduits() {
    }

    /** Любое изменение проводов или портов: кэши путей в этом мире устарели. */
    public static void invalidate(Level level) {
        GENERATION.computeIfAbsent(level, l -> new long[1])[0]++;
    }

    public static long generation(Level level) {
        return GENERATION.computeIfAbsent(level, l -> new long[1])[0];
    }

    /** Кусок пути: труба и сторона, с которой в неё входит поток. */
    public record Step(BlockPos pos, Direction from) {
    }

    /** Приёмник и путь до него по проводам (пустой, если стоит вплотную к порту). */
    public record Target(BlockPos pos, Direction side, List<Step> path) {
    }

    /** Все приёмники от грани порта: сосед напрямую или через провода нужного вида. */
    public static List<Target> targets(ServerLevel level, BlockPos port, Direction side, MachineSpec.Kind kind) {
        List<Target> out = new ArrayList<>();
        BlockPos first = port.relative(side);
        BlockState state = level.getBlockState(first);
        if (!(state.getBlock() instanceof ConduitBlock c && c.kind() == kind)) {
            if (hasStorage(level, first, side.getOpposite(), kind)) out.add(new Target(first, side.getOpposite(), List.of()));
            return out;
        }
        // обход в ширину с памятью «откуда пришли»: из неё собирается путь до каждого приёмника
        Map<BlockPos, Step> came = new HashMap<>();
        Map<BlockPos, BlockPos> parent = new HashMap<>();
        ArrayDeque<BlockPos> queue = new ArrayDeque<>();
        came.put(first, new Step(first, side.getOpposite()));
        queue.add(first);
        while (!queue.isEmpty() && came.size() < MAX_NODES) {
            BlockPos at = queue.poll();
            for (Direction d : Direction.values()) {
                BlockPos next = at.relative(d).immutable();
                if (next.equals(port)) continue;
                BlockState ns = level.getBlockState(next);
                if (ns.getBlock() instanceof ConduitBlock nc && nc.kind() == kind) {
                    if (!came.containsKey(next)) {
                        came.put(next, new Step(next, d.getOpposite()));
                        parent.put(next, at);
                        queue.add(next);
                    }
                } else if (hasStorage(level, next, d.getOpposite(), kind)) {
                    List<Step> path = new ArrayList<>();
                    for (BlockPos p = at; p != null; p = parent.get(p)) path.add(came.get(p));
                    out.add(new Target(next, d.getOpposite(), path));
                }
            }
        }
        return out;
    }

    public static boolean hasStorage(Level level, BlockPos pos, Direction side, MachineSpec.Kind kind) {
        return switch (kind) {
            case ITEM -> ItemStorage.SIDED.find(level, pos, side) != null;
            case FLUID -> FluidStorage.SIDED.find(level, pos, side) != null;
            case ENERGY -> EnergyStorage.SIDED.find(level, pos, side) != null;
        };
    }

    private static void markFlow(ServerLevel level, Target t, FluidVariant fluid) {
        long now = level.getGameTime();
        for (Step step : t.path()) {
            if (level.getBlockEntity(step.pos()) instanceof FluidPipeBlockEntity pipe) pipe.mark(fluid.getFluid(), step.from(), now);
        }
    }

    /** Передать по списку приёмников: каждому не больше равной доли, чтобы нехватка делилась поровну. */
    public static <T> long push(ServerLevel level, Storage<T> from, List<Target> targets, MachineSpec.Kind kind, long budget) {
        if (targets.isEmpty()) return 0;
        long moved = 0;
        long share = Math.max(1, budget / targets.size());
        for (Target t : targets) {
            @SuppressWarnings("unchecked")
            Storage<T> to = (Storage<T>) (kind == MachineSpec.Kind.ITEM ? ItemStorage.SIDED.find(level, t.pos(), t.side())
                    : FluidStorage.SIDED.find(level, t.pos(), t.side()));
            if (to == null || to == from) continue;
            Object[] last = new Object[1];
            long now = StorageUtil.move(from, to, v -> {
                last[0] = v;
                return true;
            }, share, null);
            moved += now;
            if (now > 0 && last[0] instanceof FluidVariant fluid) markFlow(level, t, fluid);
        }
        return moved;
    }
}
