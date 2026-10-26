package dev.warpbound.test;

import dev.warpbound.Warpbound;
import dev.warpbound.core.WarpboundBlocks;
import dev.warpbound.ship.Ship;
import dev.warpbound.ship.ShipDestination;
import dev.warpbound.ship.ShipInteriors;
import dev.warpbound.ship.ShipNavigation;
import dev.warpbound.ship.ShipRegistry;
import dev.warpbound.ship.ShipService;
import dev.warpbound.ship.ShipState;
import net.fabricmc.fabric.api.gametest.v1.FabricGameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;

/** Автотесты корабля: интерьер из отсеков и навигация. */
public class ShipGameTest implements FabricGameTest {
    @GameTest(template = EMPTY_STRUCTURE, timeoutTicks = 40, batch = "ship")
    public void interiorIsBuiltFromCompartments(GameTestHelper helper) {
        // Тестовый сервер не создаёт измерение интерьеров — строим в тестовом мире
        var interior = helper.getLevel();
        BlockPos o = helper.absolutePos(new BlockPos(0, 4, 0));
        helper.assertTrue(ShipInteriors.buildFromLayout(interior, o, ShipService.DEFAULT_LAYOUT), "раскладка крейсера должна собраться");
        helper.assertTrue(interior.getBlockState(o.offset(0, 1, 22)).is(WarpboundBlocks.NAV_TABLE), "навигационный стол на мостике");
        helper.assertTrue(interior.getBlockState(o.offset(0, 2, 17)).is(WarpboundBlocks.COMMAND_CONSOLE), "командный пульт перед троном");
        helper.assertTrue(interior.getBlockState(o.offset(-8, 0, 4)).is(WarpboundBlocks.TELEPORTARIUM_PAD), "площадка телепортариума");
        helper.assertTrue(interior.getBlockState(o.offset(0, 1, -29)).is(WarpboundBlocks.REACTOR_CORE), "ядро реактора там, куда указывает раскладка");
        BlockPos spawn = o.offset(0, 1, -6);
        helper.assertTrue(interior.getBlockState(spawn).isAir() && interior.getBlockState(spawn.above()).isAir(), "точка появления свободна");
        helper.assertFalse(interior.getBlockState(spawn.below()).isAir(), "под точкой появления пол");
        helper.succeed();
    }

    @GameTest(template = EMPTY_STRUCTURE, timeoutTicks = 40, batch = "ship")
    public void jumpSetsCourseAndArrives(GameTestHelper helper) {
        var server = helper.getLevel().getServer();
        Ship ship = ShipRegistry.get(server).create(java.util.UUID.randomUUID(), "Тест");
        ship.location = Warpbound.id("somewhere_else");

        helper.assertTrue(ShipNavigation.plotCourse(ship, ShipDestination.HOME), "курс должен проложиться");
        helper.assertTrue(ship.state == ShipState.ENTERING, "прыжок должен начаться, а состояние " + ship.state);
        helper.assertTrue(ShipDestination.HOME.equals(ship.destination), "цель — родной мир");
        // Перемотка: сразу к концу выхода из варпа
        ship.state = ShipState.EXITING;
        ship.stateTicks = 100_000;
        helper.runAfterDelay(2, () -> {
            helper.assertTrue(ship.state == ShipState.ORBIT, "корабль на орбите");
            helper.assertTrue(ShipDestination.HOME.equals(ship.location), "корабль на орбите цели, а не " + ship.location);
            helper.assertTrue(ship.destination == null, "курс сброшен");
            helper.succeed();
        });
    }
}
