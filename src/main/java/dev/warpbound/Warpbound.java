package dev.warpbound;

import dev.warpbound.chaos.ChaosAttachments;
import dev.warpbound.chaos.ChaosLogic;
import dev.warpbound.command.WarpboundCommands;
import dev.warpbound.config.WarpboundConfig;
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
        WarpboundNetwork.registerPayloads();
        ChaosLogic.registerEvents();
        ShipTicker.register();
        WarpboundCommands.register();
        LOG.info("Warpbound: варп открыт");
    }
}
