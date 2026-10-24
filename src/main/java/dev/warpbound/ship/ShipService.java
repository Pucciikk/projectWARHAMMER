package dev.warpbound.ship;

import dev.warpbound.Warpbound;
import dev.warpbound.config.WarpboundConfig;
import dev.warpbound.network.ShipStatePayload;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;

import java.util.List;
import java.util.Optional;

/** Операции над кораблями: создание, вход, выход, запуск перехода. */
public final class ShipService {
    /** В Сезоне 1 все корабли — фрегаты. */
    public static final ResourceLocation DEFAULT_LAYOUT = Warpbound.id("frigate");

    private ShipService() {
    }

    public static Ship createFor(ServerPlayer player, String name) {
        MinecraftServer server = player.server;
        ShipRegistry registry = ShipRegistry.get(server);
        Optional<Ship> existing = registry.ownedBy(player.getUUID());
        if (existing.isPresent()) return existing.get();

        Ship ship = registry.create(player.getUUID(), name);
        setDock(ship, player);
        ServerLevel interior = ShipInteriors.level(server);
        if (ShipInteriors.buildFromLayout(interior, ship.plot, DEFAULT_LAYOUT)) {
            ship.layout = DEFAULT_LAYOUT;
        } else {
            ShipInteriors.buildPlaceholderHull(interior, ship.plot);
        }
        registry.setDirty();
        return ship;
    }

    private static void setDock(Ship ship, ServerPlayer player) {
        ship.dockDimension = player.level().dimension().location();
        ship.dockX = player.getX();
        ship.dockY = player.getY();
        ship.dockZ = player.getZ();
    }

    public static void enter(ServerPlayer player, Ship ship) {
        ServerLevel interior = ShipInteriors.level(player.server);
        if (!ShipInteriors.isInterior(player.level())) {
            // Пока корабль на орбите, «док» сдвигается туда, откуда поднялся игрок
            if (ship.state == ShipState.ORBIT) setDock(ship, player);
        }
        BlockPos spawn = ShipInteriors.spawn(ship);
        player.teleportTo(interior, spawn.getX() + 0.5, spawn.getY(), spawn.getZ() + 0.5, 0f, 0f);
        ShipRegistry.get(player.server).setDirty();
        sync(player);
    }

    /** Высадка в точку дока. Во время варпа выйти нельзя. */
    public static boolean leave(ServerPlayer player, Ship ship) {
        if (ship.state != ShipState.ORBIT) return false;
        ServerLevel target = ship.dockDimension == null ? null
                : player.server.getLevel(ResourceKey.create(Registries.DIMENSION, ship.dockDimension));
        if (target == null) target = player.server.overworld();
        player.teleportTo(target, ship.dockX, ship.dockY, ship.dockZ, player.getYRot(), player.getXRot());
        sync(player);
        return true;
    }

    public static boolean startWarp(Ship ship, int transitSeconds) {
        if (ship.state != ShipState.ORBIT) return false;
        ship.state = ShipState.ENTERING;
        ship.stateTicks = 0;
        ship.transitTicks = Math.max(1, transitSeconds) * 20;
        return true;
    }

    public static boolean abortWarp(Ship ship) {
        if (ship.state != ShipState.TRANSIT && ship.state != ShipState.ENTERING) return false;
        ship.state = ShipState.EXITING;
        ship.stateTicks = 0;
        return true;
    }

    /** Корабль, на борту которого сейчас игрок (по координате в измерении интерьеров). */
    public static Optional<Ship> shipAboard(ServerPlayer player) {
        if (!ShipInteriors.isInterior(player.level())) return Optional.empty();
        return ShipRegistry.get(player.server).byPlot(ShipInteriors.plotAt(player.getX()));
    }

    public static List<ServerPlayer> crew(MinecraftServer server, Ship ship) {
        ServerLevel interior = ShipInteriors.level(server);
        if (interior == null) return List.of();
        return interior.players().stream().filter(p -> ShipInteriors.plotAt(p.getX()) == ship.plot).toList();
    }

    public static int durationTicks(Ship ship) {
        WarpboundConfig cfg = WarpboundConfig.get();
        return switch (ship.state) {
            case ENTERING -> cfg.warpEnterSeconds * 20;
            case TRANSIT -> ship.transitTicks > 0 ? ship.transitTicks : cfg.warpTransitSeconds * 20;
            case EXITING -> cfg.warpExitSeconds * 20;
            case ORBIT -> 1;
        };
    }

    public static ShipStatePayload payload(Ship ship) {
        float progress = Math.min(1f, ship.stateTicks / (float) durationTicks(ship));
        return new ShipStatePayload(true, ship.state.ordinal(), progress, ship.field, ship.storm);
    }

    public static void sync(ServerPlayer player) {
        ShipStatePayload payload = shipAboard(player).map(ShipService::payload).orElse(ShipStatePayload.NOT_ABOARD);
        ServerPlayNetworking.send(player, payload);
    }
}
