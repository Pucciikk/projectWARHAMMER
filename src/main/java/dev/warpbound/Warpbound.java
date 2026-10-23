package dev.warpbound;

import dev.warpbound.chaos.ChaosAttachments;
import dev.warpbound.chaos.ChaosLogic;
import dev.warpbound.command.WarpboundCommands;
import dev.warpbound.config.WarpboundConfig;
import dev.warpbound.core.WarpboundBlocks;
import dev.warpbound.core.WarpboundItems;
import dev.warpbound.player.PlayerAttachments;
import dev.warpbound.quest.QuestManager;
import dev.warpbound.quest.StoryDirector;
import dev.warpbound.start.CrashSite;
import dev.warpbound.team.TeamCommands;
import dev.warpbound.entity.WarpboundEntities;
import dev.warpbound.network.WarpboundNetwork;
import dev.warpbound.ship.ShipTicker;
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
        WarpboundEntities.register();
        WarpboundItems.register();
        WarpboundNetwork.registerPayloads();
        ChaosLogic.registerEvents();
        ShipTicker.register();
        WarpboundCommands.register();
        TeamCommands.register();
        QuestManager.register();
        StoryDirector.register();
        CrashSite.register();
        LOG.info("Warpbound: варп открыт");
    }
}
