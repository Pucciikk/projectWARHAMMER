package dev.warpbound.industry;

import dev.warpbound.core.WarpboundBlockEntities;
import dev.warpbound.industry.machine.ChainMachines;
import dev.warpbound.industry.machine.ChainMachineMenu;
import dev.warpbound.industry.machine.MachineRecipe;
import dev.warpbound.industry.machine.MachineSpec;
import dev.warpbound.industry.machine.MachineTanks;
import dev.warpbound.industry.machine.PortedMachine;
import dev.warpbound.industry.machine.PortPumps;
import dev.warpbound.multiblock.MachineCoreBlockEntity;
import net.fabricmc.fabric.api.screenhandler.v1.ExtendedScreenHandlerFactory;
import net.fabricmc.fabric.api.transfer.v1.fluid.FluidConstants;
import net.fabricmc.fabric.api.transfer.v1.fluid.FluidVariant;
import net.fabricmc.fabric.api.transfer.v1.item.InventoryStorage;
import net.fabricmc.fabric.api.transfer.v1.item.ItemVariant;
import net.fabricmc.fabric.api.transfer.v1.storage.Storage;
import net.fabricmc.fabric.api.transfer.v1.storage.base.CombinedStorage;
import net.fabricmc.fabric.api.transfer.v1.storage.base.FilteringStorage;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.ContainerHelper;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.AbstractFurnaceBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.material.Fluids;
import org.jetbrains.annotations.Nullable;
import team.reborn.energy.api.EnergyStorage;
import team.reborn.energy.api.base.SimpleEnergyStorage;

import java.util.ArrayList;
import java.util.List;

/**
 * Одна сущность на все машины цепочки: модель, шаблон, рецепты и порты берутся по имени блока.
 * Слоты: 0–5 входы, 6–8 выходы. Баки: 2 входа и 4 выхода; сколько из них действует — из описания машины.
 */
public class ChainMachineBlockEntity extends MachineCoreBlockEntity
        implements PortedMachine, ExtendedScreenHandlerFactory<ChainMachineMenu.Init> {
    public static final int SLOTS_IN = 6, SLOTS_OUT = 3, TANKS_IN = 2, TANKS_OUT = 4;
    private static final long ENERGY_BUFFER = 16_000;
    /** Как часто искать рецепт, если вход не менялся. */
    private static final int RECHECK = 20;

    private final SimpleContainer items = new SimpleContainer(SLOTS_IN + SLOTS_OUT) {
        @Override
        public boolean canPlaceItem(int slot, ItemStack stack) {
            return slot < SLOTS_IN && acceptsItem(slot, stack.getItem());
        }

        @Override
        public void setChanged() {
            super.setChanged();
            dirty = true;
            ChainMachineBlockEntity.this.setChanged();
        }
    };
    private final InventoryStorage itemStore = InventoryStorage.of(items, null);
    private final Storage<ItemVariant> itemsIn;
    private final Storage<ItemVariant> itemsOut;
    private final MachineTanks tanks = new MachineTanks(TANKS_IN, TANKS_OUT, this::acceptsFluid, this::setChanged);
    private final SimpleEnergyStorage energyStore = new SimpleEnergyStorage(ENERGY_BUFFER, ENERGY_BUFFER, ENERGY_BUFFER) {
        @Override
        protected void onFinalCommit() {
            ChainMachineBlockEntity.this.setChanged();
        }
    };
    private final EnergyStorage energyPort = new EnergyStorage() {
        @Override
        public long insert(long max, net.fabricmc.fabric.api.transfer.v1.transaction.TransactionContext tx) {
            return generates() ? 0 : energyStore.insert(max, tx);
        }

        @Override
        public long extract(long max, net.fabricmc.fabric.api.transfer.v1.transaction.TransactionContext tx) {
            return generates() ? energyStore.extract(max, tx) : 0;
        }

        @Override
        public long getAmount() {
            return energyStore.getAmount();
        }

        @Override
        public long getCapacity() {
            return energyStore.getCapacity();
        }

        @Override
        public boolean supportsInsertion() {
            return !generates();
        }

        @Override
        public boolean supportsExtraction() {
            return generates();
        }
    };
    private final PortPumps pump = new PortPumps();

    @Nullable
    private MachineRecipe recipe;
    private boolean dirty = true;
    private double progress;
    private int burn, burnTotal;
    /** Дробная часть сожжённых мБ: расход меньше 1 мБ за тик не должен пропадать. */
    private double fuelDebt;
    /** Что показать на экране машины: см. ChainMachineMenu.STATUS_*. На сервере не сохраняется, считается каждый тик. */
    private int status = ChainMachineMenu.STATUS_IDLE;
    /** Выбранный рецепт: -1 — первый подходящий. Нужен, когда из одного входа можно сделать разное (прокатный стан). */
    private int selected = -1;
    private int cycles;

    private final ContainerData data = new ContainerData() {
        @Override
        public int get(int i) {
            return switch (i) {
                case ChainMachineMenu.D_PROGRESS -> recipe == null ? 0 : (int) (1000 * progress / recipe.ticks());
                case ChainMachineMenu.D_ENERGY -> (int) (1000 * energyStore.getAmount() / ENERGY_BUFFER);
                case ChainMachineMenu.D_BURN -> burnTotal == 0 ? 0 : 1000 * burn / burnTotal;
                case ChainMachineMenu.D_SELECTED -> selected;
                case ChainMachineMenu.D_RECIPES -> ChainMachines.recipes(definitionId()).size();
                case ChainMachineMenu.D_OUTPUT -> selectedOutput();
                case ChainMachineMenu.D_STATUS -> status;
                case ChainMachineMenu.D_ACTIVE -> recipe == null ? -1 : ChainMachines.recipes(definitionId()).indexOf(recipe);
                default -> tanks.dataAt(i - ChainMachineMenu.D_TANKS);
            };
        }

        @Override
        public void set(int i, int value) {
        }

        @Override
        public int getCount() {
            return ChainMachineMenu.DATA_SIZE;
        }
    };

    public ChainMachineBlockEntity(BlockPos pos, BlockState state) {
        this(WarpboundBlockEntities.CHAIN_MACHINE, pos, state);
    }

    protected ChainMachineBlockEntity(net.minecraft.world.level.block.entity.BlockEntityType<?> type, BlockPos pos, BlockState state) {
        super(type, pos, state, BuiltInRegistries.BLOCK.getKey(state.getBlock()));
        List<Storage<ItemVariant>> in = new ArrayList<>(), out = new ArrayList<>();
        for (int i = 0; i < SLOTS_IN; i++) in.add(FilteringStorage.insertOnlyOf(itemStore.getSlot(i)));
        for (int i = 0; i < SLOTS_OUT; i++) out.add(FilteringStorage.extractOnlyOf(itemStore.getSlot(SLOTS_IN + i)));
        itemsIn = new CombinedStorage<>(in);
        itemsOut = new CombinedStorage<>(out);
    }

    public SimpleContainer items() {
        return items;
    }

    public MachineTanks tanks() {
        return tanks;
    }

    @Nullable
    private MachineSpec spec() {
        return ChainMachines.spec(definitionId());
    }

    private boolean generates() {
        MachineSpec s = spec();
        return s != null && s.energyOutput() > 0;
    }

    private boolean acceptsItem(int slot, Item item) {
        MachineSpec s = spec();
        if (s == null || slot >= s.slotsIn()) return false;
        if (s.kind().equals("generator")) return AbstractFurnaceBlockEntity.getFuel().containsKey(item);
        for (MachineRecipe r : ChainMachines.recipes(definitionId())) {
            for (MachineRecipe.ItemIn in : r.itemsIn()) if (in.item() == item) return true;
        }
        return false;
    }

    private boolean acceptsFluid(int tank, FluidVariant variant) {
        MachineSpec s = spec();
        if (s == null || tank >= s.tanksIn()) return false;
        if (s.kind().equals("fluid_generator")) return s.fuelFluids().containsKey(BuiltInRegistries.FLUID.getKey(variant.getFluid()).toString());
        for (MachineRecipe r : ChainMachines.recipes(definitionId())) {
            for (MachineRecipe.FluidAmount in : r.fluidsIn()) if (variant.isOf(in.fluid())) return true;
        }
        return false;
    }

    @Override
    public String modelName() {
        return BuiltInRegistries.BLOCK.getKey(getBlockState().getBlock()).getPath();
    }

    @Override
    public boolean isWorking() {
        return getBlockState().getValue(BlockStateProperties.LIT);
    }

    @Override
    public void tickFormed(ServerLevel level) {
        MachineSpec s = spec();
        if (s == null) return;
        boolean running = switch (s.kind()) {
            case "generator" -> tickGenerator(s);
            case "fluid_generator" -> tickFluidGenerator(s);
            case "source" -> tickSource(s, level);
            default -> tickProcessor(s, level);
        };
        setLit(level, running);
        pump.run(level, this, s, this, s.energyOutput() * 10L);
    }

    private boolean tickGenerator(MachineSpec s) {
        status = burn > 0 ? ChainMachineMenu.STATUS_RUNNING
                : energyStore.getAmount() >= ENERGY_BUFFER ? ChainMachineMenu.STATUS_BUFFER_FULL : ChainMachineMenu.STATUS_NO_FUEL;
        if (burn <= 0 && energyStore.getAmount() < ENERGY_BUFFER) {
            ItemStack fuel = items.getItem(0);
            Integer time = AbstractFurnaceBlockEntity.getFuel().get(fuel.getItem());
            if (time != null && !fuel.isEmpty()) {
                burn = burnTotal = time;
                fuel.shrink(1);
                items.setChanged();
                status = ChainMachineMenu.STATUS_RUNNING;
            }
        }
        if (burn <= 0) return false;
        burn--;
        energyStore.amount = Math.min(ENERGY_BUFFER, energyStore.getAmount() + s.energyOutput());
        setChanged();
        return true;
    }

    /** Прометиевый генераториум: мощность постоянная, расход зависит от топлива. Буфер полон — топливо не тратится. */
    private boolean tickFluidGenerator(MachineSpec s) {
        if (energyStore.getAmount() >= ENERGY_BUFFER) {
            status = ChainMachineMenu.STATUS_BUFFER_FULL;
            return false;
        }
        status = ChainMachineMenu.STATUS_NO_FUEL;
        for (var fuel : s.fuelFluids().entrySet()) {
            net.minecraft.world.level.material.Fluid fluid = BuiltInRegistries.FLUID.get(net.minecraft.resources.ResourceLocation.parse(fuel.getKey()));
            double due = fuelDebt + fuel.getValue() / 20.0;
            int whole = (int) due;
            if (!tanks.hasIn(fluid, Math.max(1, whole))) continue;
            if (whole > 0) tanks.drainIn(fluid, whole);
            fuelDebt = due - whole;
            status = ChainMachineMenu.STATUS_RUNNING;
            energyStore.amount = Math.min(ENERGY_BUFFER, energyStore.getAmount() + s.energyOutput());
            setChanged();
            return true;
        }
        return false;
    }

    /** Водозабор: у воды работает в полную силу, в сухом месте — как колодец, вчетверо слабее. */
    private boolean tickSource(MachineSpec s, ServerLevel level) {
        double speed = powerFraction(s);
        status = tanks.outFull(0) ? ChainMachineMenu.STATUS_OUTPUT_FULL : speed <= 0 ? ChainMachineMenu.STATUS_NO_POWER : ChainMachineMenu.STATUS_RUNNING;
        if (speed <= 0 || tanks.outFull(0)) return false;
        boolean nearWater = false;
        for (BlockPos p : BlockPos.betweenClosed(worldPosition.offset(-3, -1, -3), worldPosition.offset(3, 0, 3))) {
            if (level.getFluidState(p).is(Fluids.WATER)) {
                nearWater = true;
                break;
            }
        }
        long droplets = (long) (s.sourceRateMb() * (FluidConstants.BUCKET / 1000) * speed * (nearWater ? 1 : 0.25));
        drawPower(s, speed);
        tanks.fill(0, FluidVariant.of(BuiltInRegistries.FLUID.get(net.minecraft.resources.ResourceLocation.parse(s.sourceFluid()))), droplets);
        return true;
    }

    private boolean tickProcessor(MachineSpec s, ServerLevel level) {
        if (recipe == null || dirty || level.getGameTime() % RECHECK == 0) {
            MachineRecipe found = findRecipe();
            if (found != recipe) progress = 0;
            recipe = found;
            dirty = false;
        }
        if (recipe == null) {
            status = blockedByOutput() ? ChainMachineMenu.STATUS_OUTPUT_FULL : ChainMachineMenu.STATUS_IDLE;
            return false;
        }
        double speed = powerFraction(s);
        status = speed <= 0 ? ChainMachineMenu.STATUS_NO_POWER : ChainMachineMenu.STATUS_RUNNING;
        if (speed <= 0) return false;
        drawPower(s, speed);
        progress += speed * speedBonus(level);
        setChanged();
        if (progress >= recipe.ticks()) {
            finish(recipe, level);
            progress = 0;
            dirty = true;
        }
        return true;
    }

    /** Во сколько раз быстрее обычного: например, рядом с техножрецом. */
    protected double speedBonus(ServerLevel level) {
        return 1;
    }

    /** Доля мощности: при просадке машина замедляется пропорционально. */
    private double powerFraction(MachineSpec s) {
        if (s.energyUse() <= 0) return 1;
        return Math.min(1, (double) energyStore.getAmount() / s.energyUse());
    }

    private void drawPower(MachineSpec s, double speed) {
        if (s.energyUse() > 0) energyStore.amount = Math.max(0, energyStore.getAmount() - (long) Math.ceil(s.energyUse() * speed));
    }

    /** Номер предмета, который делает выбранный рецепт; -1, если выбора нет или на выходе только жидкость. */
    private int selectedOutput() {
        List<MachineRecipe> all = ChainMachines.recipes(definitionId());
        if (selected < 0 || selected >= all.size() || all.get(selected).itemsOut().isEmpty()) return -1;
        return BuiltInRegistries.ITEM.getId(all.get(selected).itemsOut().get(0).item());
    }

    /** Следующий или предыдущий рецепт по кругу, через положение «авто». */
    public void cycleRecipe(int step) {
        int n = ChainMachines.recipes(definitionId()).size();
        if (n < 2) return;
        selected = Math.floorMod(selected + 1 + step, n + 1) - 1;
        recipe = null;
        progress = 0;
        dirty = true;
        setChanged();
    }

    public void selectRecipe(int index) {
        selected = index;
        recipe = null;
        progress = 0;
        dirty = true;
    }

    @Nullable
    private MachineRecipe findRecipe() {
        List<MachineRecipe> all = ChainMachines.recipes(definitionId());
        if (selected >= 0 && selected < all.size()) {
            MachineRecipe r = all.get(selected);
            return hasInputs(r) && outputsFit(r) ? r : null;
        }
        for (MachineRecipe r : all) {
            if (hasInputs(r) && outputsFit(r)) return r;
        }
        return null;
    }

    /** Сырьё есть, но выход занят: игрок должен забрать продукцию. */
    private boolean blockedByOutput() {
        List<MachineRecipe> all = ChainMachines.recipes(definitionId());
        if (selected >= 0 && selected < all.size()) return hasInputs(all.get(selected)) && !outputsFit(all.get(selected));
        for (MachineRecipe r : all) if (hasInputs(r) && !outputsFit(r)) return true;
        return false;
    }

    private boolean hasInputs(MachineRecipe r) {
        for (MachineRecipe.ItemIn in : r.itemsIn()) {
            int have = 0;
            for (int i = 0; i < SLOTS_IN; i++) if (items.getItem(i).is(in.item())) have += items.getItem(i).getCount();
            if (have < in.count()) return false;
        }
        for (MachineRecipe.FluidAmount in : r.fluidsIn()) if (!tanks.hasIn(in.fluid(), in.mb())) return false;
        return true;
    }

    private boolean outputsFit(MachineRecipe r) {
        for (MachineRecipe.ItemOut out : r.itemsOut()) {
            boolean fits = false;
            for (int i = SLOTS_IN; i < SLOTS_IN + SLOTS_OUT && !fits; i++) {
                ItemStack st = items.getItem(i);
                fits = st.isEmpty() || (st.is(out.item()) && st.getCount() + out.count() <= st.getMaxStackSize());
            }
            if (!fits) return false;
        }
        for (MachineRecipe.FluidAmount out : r.fluidsOut()) if (!tanks.outFits(out.fluid(), out.mb())) return false;
        return true;
    }

    /** Для автотестов и отладки: сколько циклов закончено и почему машина стоит. */
    public int cycles() {
        return cycles;
    }

    public String debugState() {
        MachineSpec s = spec();
        return "собрана " + isFormed() + ", рецепт " + (recipe != null) + ", ход " + (int) progress + ", энергия " + energyStore.getAmount()
                + ", расход " + (s == null ? "нет описания" : s.energyUse()) + ", слоты " + items.getItems();
    }

    private void finish(MachineRecipe r, ServerLevel level) {
        if (!hasInputs(r) || !outputsFit(r)) return;
        cycles++;
        for (MachineRecipe.ItemIn in : r.itemsIn()) {
            int left = in.count();
            for (int i = 0; i < SLOTS_IN && left > 0; i++) {
                ItemStack st = items.getItem(i);
                if (!st.is(in.item())) continue;
                int take = Math.min(left, st.getCount());
                st.shrink(take);
                left -= take;
            }
        }
        for (MachineRecipe.FluidAmount in : r.fluidsIn()) tanks.drainIn(in.fluid(), in.mb());
        for (MachineRecipe.ItemOut out : r.itemsOut()) {
            if (out.chance() < 1 && level.random.nextDouble() >= out.chance()) continue;
            for (int i = SLOTS_IN; i < SLOTS_IN + SLOTS_OUT; i++) {
                ItemStack st = items.getItem(i);
                if (st.isEmpty()) {
                    items.setItem(i, new ItemStack(out.item(), out.count()));
                    break;
                }
                if (st.is(out.item()) && st.getCount() + out.count() <= st.getMaxStackSize()) {
                    st.grow(out.count());
                    break;
                }
            }
        }
        for (MachineRecipe.FluidAmount out : r.fluidsOut()) tanks.fillOut(out.fluid(), out.mb());
        items.setChanged();
    }

    @Override
    public void onUnformed(ServerLevel level) {
        setLit(level, false);
        dev.warpbound.industry.machine.Conduits.invalidate(level);
    }

    @Override
    public void onFormed(ServerLevel level) {
        dev.warpbound.industry.machine.Conduits.invalidate(level);
        dev.warpbound.industry.machine.PortPumps.refreshNeighbours(level, this);
        sync();
    }

    private void setLit(ServerLevel level, boolean lit) {
        BlockState state = getBlockState();
        if (state.getValue(BlockStateProperties.LIT) != lit) {
            level.setBlock(getBlockPos(), state.setValue(BlockStateProperties.LIT, lit), Block.UPDATE_ALL);
        }
    }

    // ---------------------------------------------------------------- порты

    @Override
    public Storage<ItemVariant> itemStorage(boolean output) {
        return output ? itemsOut : itemsIn;
    }

    @Override
    public Storage<FluidVariant> fluidStorage(boolean output) {
        return output ? tanks.outPort() : tanks.inPort();
    }

    @Override
    public EnergyStorage energyStorage() {
        return energyPort;
    }

    @Override
    public long[] clientPorts() {
        return clientPortCache;
    }

    private long[] clientPortCache = new long[0];

    // ---------------------------------------------------------------- окно

    @Override
    public Component getDisplayName() {
        return getBlockState().getBlock().getName();
    }

    @Override
    public ChainMachineMenu.Init getScreenOpeningData(ServerPlayer player) {
        MachineSpec s = spec();
        return s == null ? new ChainMachineMenu.Init(0, 0, 0, 0, false, false, 0, List.of())
                : new ChainMachineMenu.Init(s.slotsIn(), s.slotsOut(), s.tanksIn(), s.tanksOut(), s.energyUse() > 0 || s.energyOutput() > 0, s.energyOutput() > 0,
                Math.max(s.energyUse(), s.energyOutput()), ChainMachines.recipes(definitionId()));
    }

    @Override
    public AbstractContainerMenu createMenu(int id, Inventory inventory, Player player) {
        return new ChainMachineMenu(id, inventory, getScreenOpeningData((ServerPlayer) player), items, data, this::cycleRecipe);
    }

    // ---------------------------------------------------------------- сохранение

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        CompoundTag inv = new CompoundTag();
        ContainerHelper.saveAllItems(inv, items.getItems(), registries);
        tag.put("items", inv);
        tanks.save(tag, registries);
        tag.putLong("energy", energyStore.getAmount());
        tag.putDouble("progress", progress);
        tag.putInt("burn", burn);
        tag.putInt("burn_total", burnTotal);
        tag.putInt("selected", selected);
    }

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        if (tag.contains("items")) ContainerHelper.loadAllItems(tag.getCompound("items"), items.getItems(), registries);
        tanks.load(tag, registries);
        energyStore.amount = tag.getLong("energy");
        progress = tag.getDouble("progress");
        burn = tag.getInt("burn");
        burnTotal = tag.getInt("burn_total");
        selected = tag.contains("selected") ? tag.getInt("selected") : -1;
        if (tag.contains("ports")) clientPortCache = tag.getLongArray("ports");
        dirty = true;
    }

    @Override
    public CompoundTag getUpdateTag(HolderLookup.Provider registries) {
        CompoundTag tag = super.getUpdateTag(registries);
        MachineSpec s = spec();
        if (s != null) tag.putLongArray("ports", dev.warpbound.industry.machine.PortPumps.pack(s));
        return tag;
    }

    /** Содержимое машины при разрушении ядра. */
    public void dropContents() {
        if (level != null) net.minecraft.world.Containers.dropContents(level, worldPosition, items);
    }
}
