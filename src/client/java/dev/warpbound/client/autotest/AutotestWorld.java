package dev.warpbound.client.autotest;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.world.Difficulty;
import net.minecraft.world.level.GameRules;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.LevelSettings;
import net.minecraft.world.level.WorldDataConfiguration;
import net.minecraft.world.level.levelgen.WorldOptions;
import net.minecraft.world.level.levelgen.presets.WorldPresets;

/** Тестовый мир автотеста: открыть существующий или создать с одинаковыми настройками, чтобы скриншоты были сравнимы. */
final class AutotestWorld {
    /** Фиксированный сид: один и тот же ландшафт у спавна при каждом пересоздании мира. */
    private static final long SEED = 20261201L;

    private AutotestWorld() {
    }

    static void open(Minecraft mc) {
        if (mc.getLevelSource().levelExists(Autotest.WORLD)) {
            Autotest.log("Открываю мир " + Autotest.WORLD);
            mc.createWorldOpenFlows().openWorld(Autotest.WORLD, () -> {
                Autotest.log("ОШИБКА: мир " + Autotest.WORLD + " не открылся");
                mc.stop();
            });
            return;
        }
        Autotest.log("Создаю мир " + Autotest.WORLD);
        GameRules rules = new GameRules();
        rules.getRule(GameRules.RULE_DAYLIGHT).set(false, null);
        rules.getRule(GameRules.RULE_WEATHER_CYCLE).set(false, null);
        rules.getRule(GameRules.RULE_DOMOBSPAWNING).set(false, null);
        LevelSettings settings = new LevelSettings(Autotest.WORLD, GameType.CREATIVE, false, Difficulty.PEACEFUL,
                true, rules, WorldDataConfiguration.DEFAULT);
        mc.createWorldOpenFlows().createFreshLevel(Autotest.WORLD, settings, new WorldOptions(SEED, false, false),
                WorldPresets::createNormalWorldDimensions, new TitleScreen());
    }
}
