package dev.warpbound.client;

import dev.warpbound.chaos.ChaosData;
import dev.warpbound.ship.ShipState;
import net.fabricmc.fabric.api.client.rendering.v1.HudRenderCallback;
import net.minecraft.client.Minecraft;

import java.util.Locale;

/** Временный отладочный HUD: состояние корабля и порча. Заменим нормальным интерфейсом. */
public final class WarpHud {
    private WarpHud() {
    }

    static void register() {
        HudRenderCallback.EVENT.register((graphics, tickCounter) -> {
            Minecraft mc = Minecraft.getInstance();
            if (mc.options.hideGui || mc.getDebugOverlay().showDebugScreen()) return;

            int y = 6;
            if (ClientShipState.aboard()) {
                ShipState state = ClientShipState.state();
                String line = state.displayName;
                if (state != ShipState.ORBIT) {
                    line += String.format(Locale.ROOT, " · %d%%", Math.round(ClientShipState.progress() * 100));
                }
                line += String.format(Locale.ROOT, " · Поле Геллера %d%% · Шторм %d%%",
                        Math.round(ClientShipState.field() * 100), Math.round(ClientShipState.storm() * 100));
                graphics.drawString(mc.font, line, 6, y, 0xFFE8C66A);
                y += 11;
            }
            ChaosData chaos = ClientChaosState.get();
            if (chaos.corruption() > 0) {
                String line = String.format(Locale.ROOT, "Порча %.0f (%s) · Скверна %.0f",
                        chaos.corruption(), chaos.stage().displayName, chaos.taint());
                graphics.drawString(mc.font, line, 6, y, 0xFFE0479A);
            }
        });
    }
}
