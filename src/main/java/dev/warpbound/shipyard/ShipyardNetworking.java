package dev.warpbound.shipyard;

import dev.warpbound.network.NavJumpPayload;
import dev.warpbound.network.ShipyardActionPayload;
import dev.warpbound.ship.ShipNavigation;
import net.minecraft.resources.ResourceLocation;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

/** Приём кнопок экранов верфи и навигационного стола. Сервер сам проверяет права и состояние. */
public final class ShipyardNetworking {
    /** Дальше этого от пульта кнопки не работают (квадрат расстояния). */
    private static final double MAX_DISTANCE_SQR = 10 * 10;

    private ShipyardNetworking() {
    }

    public static void register() {
        ServerPlayNetworking.registerGlobalReceiver(NavJumpPayload.TYPE, (payload, context) -> {
            ResourceLocation target = ResourceLocation.tryParse(payload.destination());
            if (target != null) ShipNavigation.jump(context.player(), target);
        });
        ServerPlayNetworking.registerGlobalReceiver(ShipyardActionPayload.TYPE, (payload, context) -> {
            var player = context.player();
            if (player.distanceToSqr(payload.pos().getCenter()) > MAX_DISTANCE_SQR) return;
            if (!(player.serverLevel().getBlockEntity(payload.pos()) instanceof ShipyardBlockEntity yard) || !yard.isFormed()) return;
            switch (payload.action()) {
                case ShipyardActionPayload.DEPOSIT -> yard.deposit(player);
                case ShipyardActionPayload.START_STAGE -> yard.startStage(player);
                case ShipyardActionPayload.LAUNCH -> yard.launch(player);
                default -> yard.sendState(player);
            }
        });
    }
}
