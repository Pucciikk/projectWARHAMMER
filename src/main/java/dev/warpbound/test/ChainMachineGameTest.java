package dev.warpbound.test;

import dev.warpbound.core.WarpboundBlocks;
import dev.warpbound.industry.ChainMachineBlockEntity;
import dev.warpbound.industry.machine.ChainMachines;
import dev.warpbound.industry.machine.MachineRecipe;
import dev.warpbound.multiblock.MultiblockHost;
import dev.warpbound.multiblock.MultiblockOrientation;
import dev.warpbound.multiblock.Multiblocks;
import net.fabricmc.fabric.api.entity.FakePlayer;
import net.fabricmc.fabric.api.gametest.v1.FabricGameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestAssertException;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Block;

import java.util.ArrayList;
import java.util.List;

/** Линия цепочки: уголь в генератор, по кабелю энергия в дробильню, руда в крошку; вода по трубе в чан. */
public class ChainMachineGameTest implements FabricGameTest {
    private static ChainMachineBlockEntity machine(ServerLevel level, BlockPos core, Block block) {
        level.setBlockAndUpdate(core, block.defaultBlockState());
        var host = (MultiblockHost) level.getBlockEntity(core);
        Multiblocks.placeAll(level, core, host.multiblock().definitionId(), new MultiblockOrientation(Direction.NORTH, false));
        host.multiblock().tryForm(FakePlayer.get(level));
        if (!host.isFormed()) throw new GameTestAssertException("машина не собралась: " + block);
        return (ChainMachineBlockEntity) level.getBlockEntity(core);
    }

    private static void line(ServerLevel level, BlockPos from, BlockPos to, Block conduit) {
        for (BlockPos p : BlockPos.betweenClosed(from, to)) {
            level.setBlock(p, conduit.defaultBlockState(), Block.UPDATE_ALL);
        }
        for (BlockPos p : BlockPos.betweenClosed(from, to)) {
            level.setBlockAndUpdate(p, ((dev.warpbound.industry.machine.ConduitBlock) conduit).connections(level, p));
        }
    }

    @GameTest(template = EMPTY_STRUCTURE, timeoutTicks = 400, batch = "chain_power")
    public void coalPowersCrusherThroughCable(GameTestHelper helper) {
        var level = helper.getLevel();
        // порт энергии сзади по центру (z+2 от ядра), кабель под ними соединяет два порта
        BlockPos genCore = helper.absolutePos(new BlockPos(2, 1, 2));
        BlockPos crushCore = helper.absolutePos(new BlockPos(7, 1, 2));
        var gen = machine(level, genCore, WarpboundBlocks.COAL_GEN);
        var crush = machine(level, crushCore, WarpboundBlocks.ORE_CRUSHER);
        line(level, genCore.offset(0, 0, 3), crushCore.offset(0, 0, 3), WarpboundBlocks.ENERGY_CABLE);
        gen.items().setItem(0, new ItemStack(Items.COAL, 4));
        crush.items().setItem(0, new ItemStack(Items.RAW_IRON, 2));
        helper.succeedWhen(() -> {
            int crushed = 0;
            for (int i = ChainMachineBlockEntity.SLOTS_IN; i < ChainMachineBlockEntity.SLOTS_IN + ChainMachineBlockEntity.SLOTS_OUT; i++) {
                if (crush.items().getItem(i).getItem() != Items.GRAVEL) crushed += crush.items().getItem(i).getCount();
            }
            helper.assertTrue(crushed >= 2, "ждём дроблёную руду: выход " + crush.items().getItems() + ", энергия " + crush.energyStorage().getAmount()
                    + ", у генератора " + gen.energyStorage().getAmount());
        });
    }

    /** Каждый рецепт каждой машины: кладём вход напрямую, даём энергию, ждём выход. Находит рецепты, которые не сходятся с машиной. */
    @GameTest(template = EMPTY_STRUCTURE, timeoutTicks = 8000, batch = "chain_all")
    public void everyRecipeRuns(GameTestHelper helper) {
        var level = helper.getLevel();
        List<Run> runs = new ArrayList<>();
        int col = 0;
        List<Block> all = new ArrayList<>(WarpboundBlocks.CHAIN_MACHINES);
        all.add(WarpboundBlocks.MECHANICUS_FORGE);
        for (Block block : all) {
            var id = net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(block);
            if (ChainMachines.recipes(id).isEmpty()) continue;
            // машины стоят рядами с запасом: самая широкая 7, самая длинная 5
            BlockPos core = helper.absolutePos(new BlockPos(4 + (col % 5) * 9, 1, 2 + (col / 5) * 8));
            col++;
            // тестовая площадка держит загруженными только свои чанки, а машинам нужен тик
            for (int dx = -1; dx <= 1; dx++) {
                for (int dz = -1; dz <= 1; dz++) level.setChunkForced((core.getX() >> 4) + dx, (core.getZ() >> 4) + dz, true);
            }
            runs.add(new Run(machine(level, core, block), ChainMachines.recipes(id)));
        }
        helper.assertTrue(runs.size() >= 25, "мало машин с рецептами: " + runs.size() + "; рецепты не загрузились?");
        int total = runs.stream().mapToInt(r -> r.recipes.size()).sum();
        helper.assertTrue(total >= 90, "мало рецептов: " + total);
        helper.succeedWhen(() -> {
            List<String> left = new ArrayList<>();
            for (Run r : runs) {
                r.step();
                if (!r.done()) left.add(r.status());
            }
            if (left.isEmpty()) {
                int cycles = runs.stream().mapToInt(r -> r.m.cycles()).sum();
                org.slf4j.LoggerFactory.getLogger("warpbound-test").info("everyRecipeRuns: машин {}, рецептов {}, циклов {}, тиков теста {}", runs.size(), total, cycles, helper.getTick());
            }
            helper.assertTrue(left.isEmpty(), "не прошли: " + left + "; сбои: " + FAILS);
            helper.assertTrue(FAILS.isEmpty(), "сбои: " + FAILS);
        });
    }

    private static final List<String> FAILS = new ArrayList<>();

    private static final class Run {
        final ChainMachineBlockEntity m;
        final List<MachineRecipe> recipes;
        int index = -1, waited, startCycles;

        Run(ChainMachineBlockEntity m, List<MachineRecipe> recipes) {
            this.m = m;
            this.recipes = recipes;
        }

        boolean done() {
            return index >= recipes.size();
        }

        String status() {
            return m.definitionId().getPath() + " рецепт " + index + " ждёт " + waited;
        }

        void start() {
            index++;
            waited = 0;
            if (done()) return;
            m.items().clearContent();
            m.tanks().clear();
            MachineRecipe r = recipes.get(index);
            int slot = 0;
            for (var in : r.itemsIn()) m.items().setItem(slot++, new ItemStack(in.item(), in.count()));
            for (var in : r.fluidsIn()) m.tanks().fillIn(in.fluid(), in.mb());
            m.selectRecipe(index);
            startCycles = m.cycles();
        }

        void step() {
            if (done()) return;
            if (index < 0) {
                start();
                return;
            }
            try (var tx = net.fabricmc.fabric.api.transfer.v1.transaction.Transaction.openOuter()) {
                m.energyStorage().insert(1000, tx);
                tx.commit();
            }
            MachineRecipe r = recipes.get(index);
            if (m.cycles() > startCycles) {
                boolean needItem = !r.itemsOut().isEmpty() && r.itemsOut().get(0).chance() >= 1;
                if (needItem) {
                    boolean got = false;
                    for (int i = ChainMachineBlockEntity.SLOTS_IN; i < ChainMachineBlockEntity.SLOTS_IN + ChainMachineBlockEntity.SLOTS_OUT; i++) {
                        if (m.items().getItem(i).is(r.itemsOut().get(0).item())) got = true;
                    }
                    if (!got) FAILS.add(m.definitionId().getPath() + "#" + index + " нет выхода " + r.itemsOut().get(0).item());
                }
                if (!r.fluidsOut().isEmpty() && m.tanks().outEmpty()) FAILS.add(m.definitionId().getPath() + "#" + index + " нет жидкости на выходе");
                start();
            } else if (++waited > r.ticks() + 60) {
                FAILS.add(m.definitionId().getPath() + "#" + index + " не закончился: " + m.debugState());
                start();
            }
        }
    }

    /** Прометиевый генераториум: жжёт прометий из бака и копит энергию, а вода в бак не заходит. */
    @GameTest(template = EMPTY_STRUCTURE, timeoutTicks = 200, batch = "chain_fuel")
    public void promethiumGeneratorBurnsFuel(GameTestHelper helper) {
        var level = helper.getLevel();
        var gen = machine(level, helper.absolutePos(new BlockPos(4, 1, 2)), WarpboundBlocks.PROMETHIUM_GEN);
        var prom = net.minecraft.core.registries.BuiltInRegistries.FLUID.get(dev.warpbound.Warpbound.id("promethium"));
        gen.tanks().fillIn(prom, 1000);
        helper.succeedWhen(() -> {
            helper.assertTrue(gen.energyStorage().getAmount() > 2000, "энергии мало: " + gen.energyStorage().getAmount());
            helper.assertTrue(gen.tanks().dataAt(0) < 1000, "топливо не тратится: " + gen.tanks().dataAt(0));
        });
    }

    /** Залежи: в каждом квадрате есть поле, центр поля — внутри поля, богатство в границах, вне поля пусто. */
    @GameTest(template = EMPTY_STRUCTURE, batch = "chain_fuel")
    public void depositsAreConsistent(GameTestHelper helper) {
        long seed = 8675309L;
        int inside = 0, total = 0;
        for (int x = -64; x < 64; x++) {
            for (int z = -64; z < 64; z++) {
                total++;
                int rich = dev.warpbound.industry.PromethiumDeposits.richness(seed, x, z);
                if (dev.warpbound.industry.PromethiumDeposits.isDeposit(seed, x, z)) {
                    inside++;
                    helper.assertTrue(rich >= 30 && rich <= 100, "богатство вне границ: " + rich);
                } else {
                    helper.assertTrue(rich == 0, "вне поля богатство " + rich);
                }
            }
        }
        // 9 чанков поля на 64 чанка квадрата
        helper.assertTrue(inside * 64 == total * 9, "полей не столько: " + inside + " из " + total);
        var c = dev.warpbound.industry.PromethiumDeposits.nearestField(seed, 3, -5);
        helper.assertTrue(dev.warpbound.industry.PromethiumDeposits.isFieldCenter(seed, c.x, c.z), "ближайшее поле не центр");
        helper.succeed();
    }

    @GameTest(template = EMPTY_STRUCTURE, timeoutTicks = 400, batch = "chain_water")
    public void waterFlowsThroughPipe(GameTestHelper helper) {
        var level = helper.getLevel();
        BlockPos intakeCore = helper.absolutePos(new BlockPos(2, 1, 2));
        BlockPos vatCore = helper.absolutePos(new BlockPos(7, 1, 2));
        var intake = machine(level, intakeCore, WarpboundBlocks.WATER_INTAKE);
        var vat = machine(level, vatCore, WarpboundBlocks.WASH_VAT);
        // энергию здесь проверять не нужно: заряжаем водозабор напрямую через его порт
        try (var tx = net.fabricmc.fabric.api.transfer.v1.transaction.Transaction.openOuter()) {
            intake.energyStorage().insert(8000, tx);
            tx.commit();
        }
        // выходной порт сзади справа (x+1), вход чана сзади слева (x-1)
        line(level, intakeCore.offset(1, 0, 3), vatCore.offset(-1, 0, 3), WarpboundBlocks.FLUID_PIPE);
        helper.succeedWhen(() -> helper.assertTrue(vat.tanks().dataAt(0) > 0,
                "ждём воду в чане: у водозабора " + intake.tanks().dataAt(ChainMachineBlockEntity.TANKS_IN * 2) + " мБ, энергия " + intake.energyStorage().getAmount()));
    }
}
