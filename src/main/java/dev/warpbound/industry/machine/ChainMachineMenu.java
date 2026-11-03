package dev.warpbound.industry.machine;

import dev.warpbound.core.WarpboundMenus;
import dev.warpbound.industry.ChainMachineBlockEntity;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.world.Container;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.SimpleContainerData;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;

import java.util.ArrayList;
import java.util.List;

/** Окно машины цепочки: входы слева, выходы справа; манометры, статус и подсказку рецепта рисует экран. */
public class ChainMachineMenu extends AbstractContainerMenu {
    public static final int D_PROGRESS = 0, D_ENERGY = 1, D_BURN = 2, D_SELECTED = 3, D_RECIPES = 4, D_OUTPUT = 5, D_STATUS = 6, D_ACTIVE = 7, D_TANKS = 8;
    public static final int DATA_SIZE = D_TANKS + (ChainMachineBlockEntity.TANKS_IN + ChainMachineBlockEntity.TANKS_OUT) * 2;
    public static final int WIDTH = 232, HEIGHT = 212;
    public static final int INV_X = 35, INV_Y = 124, HOTBAR_Y = 184;
    /** Середина рабочей зоны по высоте и колонки слотов: один столбец стоит вплотную к стрелке. */
    public static final int MID_Y = 58, IN_X_WIDE = 62, IN_X_NARROW = 80, OUT_X = 146;

    /** Состояние машины для экрана. */
    public static final int STATUS_IDLE = 0, STATUS_RUNNING = 1, STATUS_NO_POWER = 2, STATUS_OUTPUT_FULL = 3, STATUS_NO_FUEL = 4, STATUS_BUFFER_FULL = 5;

    /** Что клиенту нужно знать заранее, чтобы разложить окно и показать рецепты. */
    public record Init(int slotsIn, int slotsOut, int tanksIn, int tanksOut, boolean usesEnergy, boolean generator, int power, List<MachineRecipe> recipes) {
        public static final StreamCodec<RegistryFriendlyByteBuf, Init> CODEC = StreamCodec.of((buf, v) -> {
            ByteBufCodecs.VAR_INT.encode(buf, v.slotsIn);
            ByteBufCodecs.VAR_INT.encode(buf, v.slotsOut);
            ByteBufCodecs.VAR_INT.encode(buf, v.tanksIn);
            ByteBufCodecs.VAR_INT.encode(buf, v.tanksOut);
            ByteBufCodecs.BOOL.encode(buf, v.usesEnergy);
            ByteBufCodecs.BOOL.encode(buf, v.generator);
            ByteBufCodecs.VAR_INT.encode(buf, v.power);
            ByteBufCodecs.VAR_INT.encode(buf, v.recipes.size());
            for (MachineRecipe r : v.recipes) writeRecipe(buf, r);
        }, buf -> {
            int si = ByteBufCodecs.VAR_INT.decode(buf), so = ByteBufCodecs.VAR_INT.decode(buf), ti = ByteBufCodecs.VAR_INT.decode(buf), to = ByteBufCodecs.VAR_INT.decode(buf);
            boolean energy = ByteBufCodecs.BOOL.decode(buf), gen = ByteBufCodecs.BOOL.decode(buf);
            int power = ByteBufCodecs.VAR_INT.decode(buf), n = ByteBufCodecs.VAR_INT.decode(buf);
            List<MachineRecipe> list = new ArrayList<>(n);
            for (int i = 0; i < n; i++) list.add(readRecipe(buf));
            return new Init(si, so, ti, to, energy, gen, power, list);
        });
    }

    private static void writeRecipe(RegistryFriendlyByteBuf buf, MachineRecipe r) {
        buf.writeDouble(r.seconds());
        ByteBufCodecs.VAR_INT.encode(buf, r.itemsIn().size());
        for (var i : r.itemsIn()) {
            ByteBufCodecs.VAR_INT.encode(buf, BuiltInRegistries.ITEM.getId(i.item()));
            ByteBufCodecs.VAR_INT.encode(buf, i.count());
        }
        ByteBufCodecs.VAR_INT.encode(buf, r.itemsOut().size());
        for (var i : r.itemsOut()) {
            ByteBufCodecs.VAR_INT.encode(buf, BuiltInRegistries.ITEM.getId(i.item()));
            ByteBufCodecs.VAR_INT.encode(buf, i.count());
            buf.writeDouble(i.chance());
        }
        writeFluids(buf, r.fluidsIn());
        writeFluids(buf, r.fluidsOut());
    }

    private static void writeFluids(RegistryFriendlyByteBuf buf, List<MachineRecipe.FluidAmount> list) {
        ByteBufCodecs.VAR_INT.encode(buf, list.size());
        for (var f : list) {
            ByteBufCodecs.VAR_INT.encode(buf, BuiltInRegistries.FLUID.getId(f.fluid()));
            ByteBufCodecs.VAR_INT.encode(buf, f.mb());
        }
    }

    private static List<MachineRecipe.FluidAmount> readFluids(RegistryFriendlyByteBuf buf) {
        int n = ByteBufCodecs.VAR_INT.decode(buf);
        List<MachineRecipe.FluidAmount> list = new ArrayList<>(n);
        for (int i = 0; i < n; i++) {
            list.add(new MachineRecipe.FluidAmount(BuiltInRegistries.FLUID.byId(ByteBufCodecs.VAR_INT.decode(buf)), ByteBufCodecs.VAR_INT.decode(buf)));
        }
        return list;
    }

    private static MachineRecipe readRecipe(RegistryFriendlyByteBuf buf) {
        double seconds = buf.readDouble();
        int n = ByteBufCodecs.VAR_INT.decode(buf);
        List<MachineRecipe.ItemIn> in = new ArrayList<>(n);
        for (int i = 0; i < n; i++) {
            in.add(new MachineRecipe.ItemIn(BuiltInRegistries.ITEM.byId(ByteBufCodecs.VAR_INT.decode(buf)), ByteBufCodecs.VAR_INT.decode(buf)));
        }
        n = ByteBufCodecs.VAR_INT.decode(buf);
        List<MachineRecipe.ItemOut> out = new ArrayList<>(n);
        for (int i = 0; i < n; i++) {
            out.add(new MachineRecipe.ItemOut(BuiltInRegistries.ITEM.byId(ByteBufCodecs.VAR_INT.decode(buf)), ByteBufCodecs.VAR_INT.decode(buf), buf.readDouble()));
        }
        List<MachineRecipe.FluidAmount> fi = readFluids(buf);
        List<MachineRecipe.FluidAmount> fo = readFluids(buf);
        return new MachineRecipe(net.minecraft.resources.ResourceLocation.withDefaultNamespace("client"), seconds, in, out, fi, fo);
    }

    private final Init init;
    private final ContainerData data;
    private final int machineSlots;
    private final java.util.function.IntConsumer cycle;

    public ChainMachineMenu(int id, Inventory inventory, Init init) {
        this(id, inventory, init, new SimpleContainer(ChainMachineBlockEntity.SLOTS_IN + ChainMachineBlockEntity.SLOTS_OUT), new SimpleContainerData(DATA_SIZE), step -> {
        });
    }

    public ChainMachineMenu(int id, Inventory inventory, Init init, Container container, ContainerData data, java.util.function.IntConsumer cycle) {
        super(WarpboundMenus.CHAIN_MACHINE, id);
        this.cycle = cycle;
        this.init = init;
        this.data = data;
        addDataSlots(data);
        for (int i = 0; i < init.slotsIn(); i++) {
            addSlot(new Slot(container, i, inX(i, init.slotsIn()), slotY(i, init.slotsIn())) {
                @Override
                public boolean mayPlace(ItemStack stack) {
                    return container.canPlaceItem(getContainerSlot(), stack);
                }
            });
        }
        for (int i = 0; i < init.slotsOut(); i++) {
            addSlot(new Slot(container, ChainMachineBlockEntity.SLOTS_IN + i, OUT_X, columnY(i, init.slotsOut())) {
                @Override
                public boolean mayPlace(ItemStack stack) {
                    return false;
                }
            });
        }
        machineSlots = init.slotsIn() + init.slotsOut();
        for (int row = 0; row < 3; row++) {
            for (int col = 0; col < 9; col++) addSlot(new Slot(inventory, col + row * 9 + 9, INV_X + col * 18, INV_Y + row * 18));
        }
        for (int col = 0; col < 9; col++) addSlot(new Slot(inventory, col, INV_X + col * 18, HOTBAR_Y));
    }

    /** До трёх входов одним столбцом у стрелки, больше — двумя столбцами. */
    private static int inX(int i, int total) {
        return total <= 3 ? IN_X_NARROW : IN_X_WIDE + (i % 2) * 18;
    }

    private static int slotY(int i, int total) {
        if (total <= 3) return columnY(i, total);
        int rows = (total + 1) / 2;
        return MID_Y - rows * 9 + (i / 2) * 18;
    }

    private static int columnY(int i, int total) {
        return MID_Y - total * 9 + i * 18;
    }

    public Init init() {
        return init;
    }

    public int value(int index) {
        return data.get(index);
    }

    public int menuInSlots() {
        return init.slotsIn();
    }

    /** Сколько слотов занимает сама машина: для экрана, чтобы рисовать им рамки и подсказки. */
    public int machineSlots() {
        return machineSlots;
    }

    /** Кнопки выбора рецепта: 0 — назад, 1 — вперёд. */
    @Override
    public boolean clickMenuButton(Player player, int id) {
        cycle.accept(id == 0 ? -1 : 1);
        return true;
    }

    @Override
    public ItemStack quickMoveStack(Player player, int index) {
        Slot slot = slots.get(index);
        if (!slot.hasItem()) return ItemStack.EMPTY;
        ItemStack stack = slot.getItem();
        ItemStack copy = stack.copy();
        if (index < machineSlots) {
            if (!moveItemStackTo(stack, machineSlots, slots.size(), true)) return ItemStack.EMPTY;
        } else if (!moveItemStackTo(stack, 0, init.slotsIn(), false)) {
            return ItemStack.EMPTY;
        }
        if (stack.isEmpty()) slot.setByPlayer(ItemStack.EMPTY);
        else slot.setChanged();
        return copy;
    }

    @Override
    public boolean stillValid(Player player) {
        return true;
    }
}
