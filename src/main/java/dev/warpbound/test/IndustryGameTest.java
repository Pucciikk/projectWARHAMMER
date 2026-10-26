package dev.warpbound.test;

import dev.warpbound.multiblock.MultiblockHost;
import dev.warpbound.multiblock.MultiblockOrientation;
import dev.warpbound.multiblock.Multiblocks;
import net.minecraft.gametest.framework.GameTestAssertException;
import net.minecraft.server.level.ServerLevel;

import dev.warpbound.core.WarpboundBlocks;
import dev.warpbound.core.WarpboundItems;
import dev.warpbound.industry.ManualPressBlock;
import dev.warpbound.industry.SalvageForgeBlockEntity;
import net.fabricmc.fabric.api.entity.FakePlayer;
import net.fabricmc.fabric.api.gametest.v1.FabricGameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;

/** Автотесты первой индустрии: ручной пресс и горн обломков (собранные мультиблоки). */
public class IndustryGameTest implements FabricGameTest {
    /** Поставить груду по шаблону вокруг ядра (лицом на север) и освятить машину. */
    private static void form(ServerLevel level, BlockPos core, FakePlayer player) {
        var host = (MultiblockHost) level.getBlockEntity(core);
        Multiblocks.placeAll(level, core, host.multiblock().definitionId(), new MultiblockOrientation(Direction.NORTH, false));
        host.multiblock().tryForm(player);
        if (!host.isFormed()) throw new GameTestAssertException("машина не собралась у " + core);
    }

    @GameTest(template = EMPTY_STRUCTURE)
    public void pressMakesPlateInFourStrokes(GameTestHelper helper) {
        var level = helper.getLevel();
        BlockPos pos = helper.absolutePos(new BlockPos(2, 1, 1));
        level.setBlockAndUpdate(pos, WarpboundBlocks.MANUAL_PRESS.defaultBlockState().setValue(ManualPressBlock.DIE, ManualPressBlock.Die.PLATE));
        FakePlayer player = FakePlayer.get(level);
        form(level, pos, player);
        ItemStack ingot = new ItemStack(WarpboundItems.PLASTEEL_INGOT, 2);
        player.setItemInHand(InteractionHand.MAIN_HAND, ingot);
        var hit = new BlockHitResult(Vec3.atCenterOf(pos), Direction.UP, pos, false);
        for (int i = 0; i < 4; i++) {
            level.getBlockState(pos).useItemOn(ingot, level, player, InteractionHand.MAIN_HAND, hit);
        }
        helper.assertTrue(ingot.getCount() == 1, "пресс должен съесть один слиток, осталось " + ingot.getCount());
        helper.assertTrue(player.getInventory().countItem(WarpboundItems.PLASTEEL_PLATE) == 1, "должна получиться пластина");
        helper.assertTrue(level.getBlockState(pos).getValue(ManualPressBlock.STROKES) == 0, "ход пресса сбрасывается");
        helper.succeed();
    }

    @GameTest(template = EMPTY_STRUCTURE, timeoutTicks = 300)
    public void forgeSmeltsHullPlating(GameTestHelper helper) {
        var level = helper.getLevel();
        BlockPos pos = helper.absolutePos(new BlockPos(2, 1, 1));
        level.setBlockAndUpdate(pos, WarpboundBlocks.SALVAGE_FORGE.defaultBlockState());
        form(level, pos, FakePlayer.get(level));
        var forge = (SalvageForgeBlockEntity) level.getBlockEntity(pos);
        forge.setItem(0, new ItemStack(WarpboundBlocks.HULL_PLATING));
        forge.setItem(1, new ItemStack(Items.COAL));
        helper.succeedWhen(() -> {
            ItemStack out = forge.getItem(2);
            helper.assertTrue(out.is(WarpboundItems.PLASTEEL_INGOT) && out.getCount() == 1, "ждём пластальной слиток: вход " + forge.getItem(0) + ", топливо " + forge.getItem(1) + ", выход " + out + ", горит " + level.getBlockState(pos));
        });
    }
}
