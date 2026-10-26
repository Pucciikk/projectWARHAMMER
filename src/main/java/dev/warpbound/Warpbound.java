package dev.warpbound;

import dev.warpbound.chaos.ChaosAttachments;
import dev.warpbound.chaos.ChaosLogic;
import dev.warpbound.command.WarpboundCommands;
import dev.warpbound.config.WarpboundConfig;
import dev.warpbound.core.WarpboundBlockEntities;
import dev.warpbound.core.WarpboundBlocks;
import dev.warpbound.core.WarpboundBuildingBlocks;
import dev.warpbound.core.WarpboundWorldgen;
import dev.warpbound.core.WarpboundMenus;
import dev.warpbound.core.WarpboundParticles;
import dev.warpbound.core.WarpboundSounds;
import dev.warpbound.core.WarpboundEffects;
import dev.warpbound.ship.ShipConsole;
import dev.warpbound.industry.ManualPressBlock;
import dev.warpbound.industry.WarpboundRecipes;
import dev.warpbound.core.WarpboundItems;
import dev.warpbound.multiblock.Multiblocks;
import dev.warpbound.player.PlayerAttachments;
import dev.warpbound.quest.QuestManager;
import dev.warpbound.quest.StoryDirector;
import dev.warpbound.start.CrashSite;
import dev.warpbound.team.TeamCommands;
import dev.warpbound.entity.WarpboundEntities;
import dev.warpbound.network.WarpboundNetwork;
import dev.warpbound.ship.ShipDestination;
import dev.warpbound.ship.ShipLayout;
import dev.warpbound.ship.ShipTicker;
import dev.warpbound.shipyard.ShipClasses;
import dev.warpbound.shipyard.ShipyardNetworking;
import net.fabricmc.api.ModInitializer;
import net.minecraft.resources.ResourceLocation;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Точка входа мода. Здесь только регистрация систем, сама логика живёт в пакетах.
 */
public class Warpbound implements ModInitializer {
    public static final String MOD_ID = "warpbound";
    public static final Logger LOG = LoggerFactory.getLogger(MOD_ID);

    public static ResourceLocation id(String path) {
        return ResourceLocation.fromNamespaceAndPath(MOD_ID, path);
    }

    @Override
    public void onInitialize() {
        WarpboundConfig.load();
        ChaosAttachments.register();
        PlayerAttachments.register();
        WarpboundBlocks.register();
        WarpboundBuildingBlocks.register();
        WarpboundWorldgen.register();
        WarpboundBlockEntities.register();
        WarpboundMenus.register();
        WarpboundRecipes.register();
        ManualPressBlock.register();
        WarpboundSounds.register();
        WarpboundEffects.register();
        WarpboundParticles.register();
        WarpboundEntities.register();
        WarpboundItems.register();
        WarpboundNetwork.registerPayloads();
        ChaosLogic.registerEvents();
        ShipTicker.register();
        ShipConsole.register();
        ShipLayout.register();
        ShipDestination.register();
        WarpboundCommands.register();
        TeamCommands.register();
        QuestManager.register();
        StoryDirector.register();
        CrashSite.register();
        Multiblocks.register();
        ShipClasses.register();
        ShipyardNetworking.register();
        LOG.info("Warpbound: варп открыт");
    }
}
