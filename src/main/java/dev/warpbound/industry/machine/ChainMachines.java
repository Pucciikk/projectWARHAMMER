package dev.warpbound.industry.machine;

import dev.warpbound.Warpbound;
import dev.warpbound.core.ChainContentList;
import dev.warpbound.core.DataRegistry;
import dev.warpbound.core.WarpboundBlockEntities;
import dev.warpbound.multiblock.MachinePartBlockEntity;
import dev.warpbound.multiblock.MultiblockCoreBlockEntity;
import dev.warpbound.multiblock.MultiblockOrientation;
import net.fabricmc.fabric.api.transfer.v1.fluid.FluidStorage;
import net.fabricmc.fabric.api.transfer.v1.item.ItemStorage;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityType;
import org.jetbrains.annotations.Nullable;
import team.reborn.energy.api.EnergyStorage;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/** Описания и рецепты машин цепочки, а также подключение их портов к Fabric Transfer API и Reborn Energy. */
public final class ChainMachines {
    public static final DataRegistry<MachineSpec> SPECS = new DataRegistry<>("machine_spec", MachineSpec.CODEC);
    public static final DataRegistry<MachineRecipe> RECIPES = new DataRegistry<>("machine_recipe", MachineRecipe.CODEC);
    private static Map<ResourceLocation, List<MachineRecipe>> byMachine = Map.of();

    private ChainMachines() {
    }

    /** Предметы и жидкости должны зарегистрироваться до загрузки датапака. */
    public static void registerContent() {
        for (String name : ChainContentList.ITEMS) {
            Registry.register(BuiltInRegistries.ITEM, Warpbound.id(name), new Item(new Item.Properties()));
        }
        for (String name : ChainContentList.FLUIDS.keySet()) {
            Registry.register(BuiltInRegistries.FLUID, Warpbound.id(name), new ChainFluid());
        }
    }

    public static void register() {
        RECIPES.onReload(reg -> {
            Map<ResourceLocation, List<MachineRecipe>> map = new HashMap<>();
            for (MachineRecipe r : reg.all().values()) map.computeIfAbsent(r.machine(), k -> new ArrayList<>()).add(r);
            byMachine = map;
        });
        BlockEntityType<?>[] types = {WarpboundBlockEntities.MACHINE_PART, WarpboundBlockEntities.CHAIN_MACHINE, WarpboundBlockEntities.PROMETHIUM_EXTRACTOR, WarpboundBlockEntities.MECHANICUS_FORGE};
        ItemStorage.SIDED.registerForBlockEntities((be, side) -> {
            MachineSpec.Port p = portAt(be, side, MachineSpec.Kind.ITEM);
            return p == null ? null : machineOf(be).itemStorage(p.output());
        }, types);
        FluidStorage.SIDED.registerForBlockEntities((be, side) -> {
            MachineSpec.Port p = portAt(be, side, MachineSpec.Kind.FLUID);
            return p == null ? null : machineOf(be).fluidStorage(p.output());
        }, types);
        EnergyStorage.SIDED.registerForBlockEntities((be, side) -> {
            MachineSpec.Port p = portAt(be, side, MachineSpec.Kind.ENERGY);
            return p == null ? null : machineOf(be).energyStorage();
        }, types);
    }

    public static List<MachineRecipe> recipes(ResourceLocation machine) {
        return byMachine.getOrDefault(machine, List.of());
    }

    @Nullable
    public static MachineSpec spec(ResourceLocation machine) {
        return SPECS.get(machine).orElse(null);
    }

    private static BlockEntity coreOf(BlockEntity be) {
        Level level = be.getLevel();
        if (level == null) return null;
        return be instanceof MachinePartBlockEntity part ? (part.bound() ? level.getBlockEntity(part.core()) : null) : be;
    }

    private static PortedMachine machineOf(BlockEntity be) {
        return (PortedMachine) coreOf(be);
    }

    /** Порт нужного вида на этой грани этого блока. Трубы цепляются только к портам. */
    @Nullable
    private static MachineSpec.Port portAt(BlockEntity be, @Nullable Direction side, MachineSpec.Kind kind) {
        if (side == null) return null;
        if (!(coreOf(be) instanceof MultiblockCoreBlockEntity core) || !(core instanceof PortedMachine) || !core.isFormed()) return null;
        MachineSpec spec = spec(core.definitionId());
        if (spec == null) return null;
        MultiblockOrientation o = core.orientation();
        for (MachineSpec.Port p : spec.ports()) {
            if (p.kind() != kind) continue;
            if (o.toWorld(core.getBlockPos(), p.offset()).equals(be.getBlockPos()) && o.rotation().rotate(p.face()) == side) return p;
        }
        return null;
    }

    /** Порт в мире: блок машины и грань наружу. */
    public record WorldPort(MachineSpec.Kind kind, boolean output, BlockPos pos, Direction side) {
    }

    public static List<WorldPort> worldPorts(MultiblockCoreBlockEntity core, MachineSpec spec) {
        List<WorldPort> out = new ArrayList<>(spec.ports().size());
        MultiblockOrientation o = core.orientation();
        for (MachineSpec.Port p : spec.ports()) {
            out.add(new WorldPort(p.kind(), p.output(), o.toWorld(core.getBlockPos(), p.offset()), o.rotation().rotate(p.face())));
        }
        return out;
    }
}
