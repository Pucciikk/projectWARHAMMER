package dev.warpbound.test;

import dev.warpbound.core.WarpboundBlocks;
import dev.warpbound.multiblock.MultiblockCoreBlock;
import dev.warpbound.multiblock.MultiblockOrientation;
import dev.warpbound.multiblock.Multiblocks;
import dev.warpbound.shipyard.ShipyardBlockEntity;
import net.fabricmc.fabric.api.entity.FakePlayer;
import net.fabricmc.fabric.api.gametest.v1.FabricGameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.world.level.block.Blocks;

/**
 * Автотесты верфи: ./gradlew runGametest. Проверяют без игрока, что рама собирается,
 * что ошибки сборки находятся, что этапы корабля появляются в доке и что старт очищает док.
 */
public class ShipyardGameTest implements FabricGameTest {
    /** Шесть этапов по паре тиков и сто тиков варп-огня — с запасом. Тесты в разных партиях: доки длинные и задели бы соседей. */
    private static final int TIMEOUT = 400;

    private static BlockPos placeConsole(GameTestHelper helper) {
        BlockPos core = helper.absolutePos(new BlockPos(0, 1, 0));
        helper.getLevel().setBlockAndUpdate(core, WarpboundBlocks.SHIPYARD_CONSOLE.defaultBlockState()
                .setValue(MultiblockCoreBlock.FACING, Direction.NORTH));
        return core;
    }

    @GameTest(template = EMPTY_STRUCTURE, timeoutTicks = 40, batch = "shipyard_missing")
    public void frameMissingIsReported(GameTestHelper helper) {
        BlockPos core = placeConsole(helper);
        var yard = (ShipyardBlockEntity) helper.getLevel().getBlockEntity(core);
        yard.tryForm(FakePlayer.get(helper.getLevel()));
        helper.assertFalse(yard.isFormed(), "верфь без рамы не должна собираться");
        helper.succeed();
    }

    @GameTest(template = EMPTY_STRUCTURE, timeoutTicks = TIMEOUT, batch = "shipyard_frigate")
    public void cruiserIsBuiltAndLaunched(GameTestHelper helper) {
        var level = helper.getLevel();
        BlockPos core = placeConsole(helper);
        // Тестовая площадка обнесена барьерами — расчистить место под док
        for (BlockPos p : BlockPos.betweenClosed(core.offset(-26, 0, 1), core.offset(26, 70, 162))) {
            level.setBlock(p, Blocks.AIR.defaultBlockState(), 2);
        }
        var yard = (ShipyardBlockEntity) level.getBlockEntity(core);
        Multiblocks.placeAll(level, core, yard.definitionId(), new MultiblockOrientation(Direction.NORTH, false));
        FakePlayer player = FakePlayer.get(level);
        yard.tryForm(player);
        helper.assertTrue(yard.isFormed(), "рама поставлена — верфь должна собраться");

        // Сломать балку нельзя — она часть освящённой машины
        BlockPos girder = yard.members().get(0);
        helper.assertTrue(Multiblocks.coreOf(level, girder).isPresent(), "балка должна быть в индексе верфи");

        var seq = helper.startSequence();
        for (int i = 0; i < 6; i++) {
            seq.thenExecute(() -> yard.debugAdvance(player)).thenIdle(2);
        }
        seq.thenExecute(() -> {
            helper.assertTrue(yard.stage() == 6, "должно быть 6 этапов, а не " + yard.stage());
            helper.assertTrue(yard.shipBlocks().size() > 1000, "корабль в доке слишком мал: " + yard.shipBlocks().size());
            BlockPos hull = yard.shipBlocks().get(yard.shipBlocks().size() / 2);
            helper.assertFalse(level.getBlockState(hull).isAir(), "блок корпуса должен стоять в мире");
            yard.launch(player);
        }).thenIdle(110).thenExecute(() -> {
            helper.assertTrue(yard.shipBlocks().isEmpty(), "после старта док должен опустеть");
            helper.assertTrue(yard.stage() == 0, "после старта верфь готова к новому кораблю");
            helper.assertTrue(level.getBlockState(core).is(WarpboundBlocks.SHIPYARD_CONSOLE), "пульт на месте");
            helper.assertFalse(level.getBlockState(core.south(5).above(2)).is(Blocks.STONE), "в доке пусто");
        }).thenSucceed();
    }

    /** Пульт смотрит на восток — док должен уйти на запад, и корабль встать внутри дока. */
    @GameTest(template = EMPTY_STRUCTURE, timeoutTicks = 60, batch = "shipyard_rotated")
    public void rotatedShipyardBuildsBehindConsole(GameTestHelper helper) {
        var level = helper.getLevel();
        BlockPos core = helper.absolutePos(new BlockPos(0, 1, 0));
        for (BlockPos p : BlockPos.betweenClosed(core.offset(-162, 0, -26), core.offset(-1, 70, 26))) {
            level.setBlock(p, Blocks.AIR.defaultBlockState(), 2);
        }
        level.setBlockAndUpdate(core, WarpboundBlocks.SHIPYARD_CONSOLE.defaultBlockState()
                .setValue(MultiblockCoreBlock.FACING, Direction.EAST));
        var yard = (ShipyardBlockEntity) level.getBlockEntity(core);
        Multiblocks.placeAll(level, core, yard.definitionId(), new MultiblockOrientation(Direction.EAST, false));
        FakePlayer player = FakePlayer.get(level);
        yard.tryForm(player);
        helper.assertTrue(yard.isFormed(), "повёрнутая рама должна собраться");
        helper.assertTrue(yard.members().stream().allMatch(p -> p.getX() < core.getX()), "рама должна лежать к западу от пульта");
        helper.startSequence().thenExecute(() -> yard.debugAdvance(player)).thenIdle(2).thenExecute(() -> {
            helper.assertFalse(yard.shipBlocks().isEmpty(), "киль должен появиться");
            helper.assertTrue(yard.shipBlocks().stream().allMatch(p -> p.getX() < core.getX() && Math.abs(p.getZ() - core.getZ()) <= 24),
                    "киль должен стоять в доке за пультом");
        }).thenSucceed();
    }
}
