package dev.warpbound.industry.machine;

import dev.warpbound.core.WarpboundMenus;
import dev.warpbound.industry.ChainMachineBlockEntity;
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

/** Окно машины цепочки: входы слева, выходы справа, полосы энергии и баков рисует экран. */
public class ChainMachineMenu extends AbstractContainerMenu {
    public static final int D_PROGRESS = 0, D_ENERGY = 1, D_BURN = 2, D_SELECTED = 3, D_RECIPES = 4, D_OUTPUT = 5, D_TANKS = 6;
    public static final int DATA_SIZE = D_TANKS + (ChainMachineBlockEntity.TANKS_IN + ChainMachineBlockEntity.TANKS_OUT) * 2;
    public static final int WIDTH = 216, HEIGHT = 196;
    private static final int INV_X = 28, INV_Y = 114;

    /** Что клиенту нужно знать заранее, чтобы разложить окно. */
    public record Init(int slotsIn, int slotsOut, int tanksIn, int tanksOut, boolean usesEnergy, boolean generator) {
        public static final StreamCodec<RegistryFriendlyByteBuf, Init> CODEC = StreamCodec.composite(
                ByteBufCodecs.VAR_INT, Init::slotsIn, ByteBufCodecs.VAR_INT, Init::slotsOut,
                ByteBufCodecs.VAR_INT, Init::tanksIn, ByteBufCodecs.VAR_INT, Init::tanksOut,
                ByteBufCodecs.BOOL, Init::usesEnergy, ByteBufCodecs.BOOL, Init::generator, Init::new);
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
            addSlot(new Slot(container, i, inX(i), inY(i)) {
                @Override
                public boolean mayPlace(ItemStack stack) {
                    return container.canPlaceItem(getContainerSlot(), stack);
                }
            });
        }
        for (int i = 0; i < init.slotsOut(); i++) {
            addSlot(new Slot(container, ChainMachineBlockEntity.SLOTS_IN + i, 134 + i % 3 * 18, 28 + i / 3 * 18) {
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
        for (int col = 0; col < 9; col++) addSlot(new Slot(inventory, col, INV_X + col * 18, INV_Y + 58));
    }

    private static int inX(int i) {
        return 62 + i % 3 * 18;
    }

    private static int inY(int i) {
        return 28 + i / 3 * 18;
    }

    public Init init() {
        return init;
    }

    public int value(int index) {
        return data.get(index);
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
