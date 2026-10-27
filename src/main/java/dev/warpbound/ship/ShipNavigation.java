package dev.warpbound.ship;

import dev.warpbound.config.WarpboundConfig;
import dev.warpbound.network.NavStatePayload;
import dev.warpbound.network.StarChartPayload;
import dev.warpbound.team.TeamRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * Навигация и высадка: навигационный стол, телепортариум, телепорт-маяк.
 * Командовать кораблём может владелец и его команда.
 */
public final class ShipNavigation {
    /** Без событий переход длится 5 минут (решено для Сезона 1). */
    public static final int CALM_TRANSIT_SECONDS = 300;

    private ShipNavigation() {
    }

    public static boolean isCrew(ServerPlayer player, Ship ship) {
        if (ship.owner.equals(player.getUUID())) return true;
        return TeamRegistry.get(player.server).find(ship.owner).map(t -> t.members.contains(player.getUUID())).orElse(false);
    }

    /** Корабль игрока: свой или корабль его команды. */
    public static Optional<Ship> shipOf(ServerPlayer player) {
        ShipRegistry registry = ShipRegistry.get(player.server);
        Optional<Ship> own = registry.ownedBy(player.getUUID());
        if (own.isPresent()) return own;
        var team = TeamRegistry.get(player.server).find(player.getUUID());
        if (team.isEmpty()) return Optional.empty();
        for (UUID member : team.get().members) {
            Optional<Ship> s = registry.ownedBy(member);
            if (s.isPresent()) return s;
        }
        return Optional.empty();
    }

    /** ПКМ по навигационному столу: показать пункты назначения. */
    public static void openTable(ServerPlayer player) {
        Ship ship = ShipService.shipAboard(player).orElse(null);
        if (ship == null || !isCrew(player, ship)) {
            player.displayClientMessage(Component.translatable("ship.warpbound.not_your_ship").withStyle(ChatFormatting.RED), true);
            return;
        }
        if (ship.state != ShipState.ORBIT) {
            player.displayClientMessage(Component.translatable("ship.warpbound.in_warp").withStyle(ChatFormatting.DARK_PURPLE), true);
            return;
        }
        List<String> ids = new ArrayList<>(), names = new ArrayList<>();
        for (var e : ShipDestination.REGISTRY.all().entrySet()) {
            if (e.getValue().level(player.server).isEmpty()) continue; // мира ещё нет на сервере
            ids.add(e.getKey().toString());
            names.add(e.getValue().name());
        }
        ServerPlayNetworking.send(player, new NavStatePayload(ids, names, ship.location.toString()));
    }

    /**
     * ПКМ по карте Империума: миры корабля с местом на карте. Смотреть можно и у причала;
     * проложить курс — только экипажу корабля на орбите.
     */
    public static void openChart(ServerPlayer player) {
        Ship ship = ShipService.shipAboard(player).orElse(null);
        boolean canJump = ship != null && isCrew(player, ship) && ship.state == ShipState.ORBIT;
        List<String> ids = new ArrayList<>(), names = new ArrayList<>();
        List<Float> xs = new ArrayList<>(), ys = new ArrayList<>();
        List<Boolean> available = new ArrayList<>();
        for (var e : ShipDestination.REGISTRY.all().entrySet()) {
            List<Float> map = e.getValue().map();
            if (map.size() < 2) continue;
            ids.add(e.getKey().toString());
            names.add(e.getValue().name());
            xs.add(map.get(0));
            ys.add(map.get(1));
            available.add(e.getValue().level(player.server).isPresent());
        }
        String current = ship != null ? ship.location.toString() : ShipDestination.HOME.toString();
        String destination = ship != null && ship.destination != null ? ship.destination.toString() : "";
        ServerPlayNetworking.send(player, new StarChartPayload(ids, names, xs, ys, available, current, destination, canJump));
    }

    /** Выбор цели на столе: начать переход. */
    public static void jump(ServerPlayer player, ResourceLocation target) {
        Ship ship = ShipService.shipAboard(player).orElse(null);
        if (ship == null || !isCrew(player, ship) || ship.state != ShipState.ORBIT) return;
        var dest = ShipDestination.REGISTRY.get(target).orElse(null);
        if (dest == null) return;
        if (dest.level(player.server).isEmpty()) {
            player.displayClientMessage(Component.translatable("chart.warpbound.unreachable", Component.translatable(dest.name()))
                    .withStyle(ChatFormatting.DARK_RED), false);
            return;
        }
        if (ship.spawnRel != null) {
            // корабль-постройка: курс только прокладывается, переход открывает капитан с пульта (вкладка «Полёт»)
            if (target.equals(ship.location)) return;
            ship.destination = target;
            ShipRegistry.get(player.server).setDirty();
            for (ServerPlayer p : ShipService.crew(player.server, ship)) {
                p.displayClientMessage(Component.translatable("flight.warpbound.course_plotted", Component.translatable(dest.name()))
                        .withStyle(ChatFormatting.GOLD), false);
            }
            return;
        }
        if (!plotCourse(ship, target)) return;
        ShipRegistry.get(player.server).setDirty();
        for (ServerPlayer p : ShipService.crew(player.server, ship)) {
            p.displayClientMessage(Component.translatable("ship.warpbound.course_set", Component.translatable(dest.name()))
                    .withStyle(ChatFormatting.GOLD), false);
        }
    }

    /** Проложить курс и начать переход. false — корабль не на орбите или уже там. */
    public static boolean plotCourse(Ship ship, ResourceLocation target) {
        if (ship.state != ShipState.ORBIT || target.equals(ship.location)) return false;
        ship.destination = target;
        int seconds = Math.min(CALM_TRANSIT_SECONDS, WarpboundConfig.get().warpTransitSeconds);
        return ShipService.startWarp(ship, seconds);
    }

    /** Площадка телепортариума: высадка на мир под кораблём. */
    public static void beamDown(ServerPlayer player) {
        Ship ship = ShipService.shipAboard(player).orElse(null);
        if (ship == null) return;
        if (ship.state != ShipState.ORBIT) {
            player.displayClientMessage(Component.translatable("ship.warpbound.teleport_in_warp").withStyle(ChatFormatting.DARK_PURPLE), true);
            return;
        }
        var dest = ShipDestination.REGISTRY.get(ship.location).orElse(null);
        ServerLevel target = dest == null ? null : dest.level(player.server).orElse(null);
        if (target == null) {
            player.displayClientMessage(Component.translatable("ship.warpbound.no_world").withStyle(ChatFormatting.RED), true);
            return;
        }
        flash(player.serverLevel(), player.blockPosition());
        BlockPos land = dest.landingPos(target, ship, target.random);
        player.teleportTo(target, land.getX() + 0.5, land.getY(), land.getZ() + 0.5, player.getYRot(), player.getXRot());
        flash(target, land);
        ShipService.sync(player);
    }

    /** Телепорт-маяк на планете: подняться на свой корабль, если он на орбите этого мира. */
    public static void beamUp(ServerPlayer player) {
        Ship ship = shipOf(player).orElse(null);
        if (ship == null) {
            player.displayClientMessage(Component.translatable("ship.warpbound.no_ship").withStyle(ChatFormatting.RED), true);
            return;
        }
        var dest = ShipDestination.REGISTRY.get(ship.location).orElse(null);
        if (ship.state != ShipState.ORBIT || dest == null || !dest.isLevel(player.level())) {
            player.displayClientMessage(Component.translatable("ship.warpbound.not_in_orbit_here").withStyle(ChatFormatting.GOLD), true);
            return;
        }
        flash(player.serverLevel(), player.blockPosition());
        ShipService.enter(player, ship);
        flash(player.serverLevel(), player.blockPosition());
    }

    /** Синяя вспышка телепорта и гул. */
    private static void flash(ServerLevel level, BlockPos pos) {
        level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, pos.getX() + 0.5, pos.getY() + 1, pos.getZ() + 0.5, 40, 0.4, 0.9, 0.4, 0.02);
        level.sendParticles(ParticleTypes.END_ROD, pos.getX() + 0.5, pos.getY() + 1, pos.getZ() + 0.5, 20, 0.3, 0.8, 0.3, 0.05);
        level.playSound(null, pos, SoundEvents.BEACON_POWER_SELECT, SoundSource.PLAYERS, 1f, 1.6f);
        level.playSound(null, pos, SoundEvents.ENDERMAN_TELEPORT, SoundSource.PLAYERS, 0.6f, 0.6f);
    }
}
