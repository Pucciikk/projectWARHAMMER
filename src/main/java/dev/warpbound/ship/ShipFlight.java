package dev.warpbound.ship;

import dev.warpbound.core.WarpboundSounds;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;

/**
 * Предстартовая подготовка корабля в космосе (вкладка «Полёт» пульта), по канону перехода в варп:
 * двигатели → Поле Геллера → бронеставни → капитан по воксу приказывает открыть разлом → отсчёт → переход.
 * Звуки — всему экипажу; тряску и движение звёзд рисует клиент по флагам корабля.
 */
public final class ShipFlight {
    /** Отсчёт «три… два… один» перед раскрытием разлома, тики. */
    private static final int COUNTDOWN = 60;
    private static final java.util.Map<Integer, Integer> COUNTDOWNS = new java.util.HashMap<>();

    private ShipFlight() {
    }

    public static boolean toggleEngines(ServerPlayer player, Ship ship) {
        if (ship.state != ShipState.ORBIT) return false;
        ship.enginesOn = !ship.enginesOn;
        var server = player.server;
        if (ship.enginesOn) {
            vox(server, ship, "flight.warpbound.vox.engines");
            sound(server, ship, WarpboundSounds.SHUTTLE_ROAR, 3f, 0.45f);
            sound(server, ship, SoundEvents.WARDEN_HEARTBEAT, 2f, 0.5f);
        } else {
            vox(server, ship, "flight.warpbound.vox.engines_off");
            sound(server, ship, SoundEvents.BEACON_DEACTIVATE, 2f, 0.5f);
        }
        return true;
    }

    public static boolean toggleGeller(ServerPlayer player, Ship ship) {
        if (ship.state != ShipState.ORBIT) return false;
        ship.gellerOn = !ship.gellerOn;
        var server = player.server;
        if (ship.gellerOn) {
            vox(server, ship, "flight.warpbound.vox.geller");
            sound(server, ship, SoundEvents.BEACON_ACTIVATE, 2.5f, 0.6f);
            sound(server, ship, SoundEvents.RAID_HORN.value(), 1.5f, 0.8f);   // сирена по палубам
        } else {
            sound(server, ship, SoundEvents.BEACON_DEACTIVATE, 2f, 0.6f);
        }
        return true;
    }

    public static boolean toggleShutters(ServerPlayer player, Ship ship) {
        ServerLevel space = ShipInteriors.level(player.server);
        if (space == null || ship.shutterPos.length == 0) return false;
        ship.shuttersClosed = !ship.shuttersClosed;
        ShipLaunch.setShutters(space, ship, ship.shuttersClosed);
        if (ship.shuttersClosed) vox(player.server, ship, "flight.warpbound.vox.shutters");
        // скрежет бронеплит
        sound(player.server, ship, SoundEvents.GRINDSTONE_USE, 2.5f, 0.4f);
        sound(player.server, ship, SoundEvents.ANVIL_USE, 1.5f, 0.5f);
        sound(player.server, ship, SoundEvents.IRON_DOOR_CLOSE, 2f, 0.5f);
        return true;
    }

    /** Чего не хватает до открытия разлома (ключ перевода) или null — всё готово. */
    public static String missing(Ship ship) {
        if (ship.state != ShipState.ORBIT) return "flight.warpbound.need.orbit";
        if (ship.destination == null) return "flight.warpbound.need.course";
        if (!ship.enginesOn) return "flight.warpbound.need.engines";
        if (!ship.gellerOn) return "flight.warpbound.need.geller";
        if (!ship.shuttersClosed && ship.shutterPos.length > 0) return "flight.warpbound.need.shutters";
        if (COUNTDOWNS.containsKey(ship.plot)) return "flight.warpbound.need.countdown";
        return null;
    }

    /** Капитан по воксу: «Внимание! Открыть варп-разлом. Храни нас Император.» — и отсчёт. */
    public static boolean openRift(ServerPlayer captain, Ship ship) {
        if (missing(ship) != null) return false;
        for (ServerPlayer p : ShipService.crew(captain.server, ship)) {
            p.displayClientMessage(Component.translatable("flight.warpbound.vox.captain", captain.getName())
                    .withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD), false);
        }
        sound(captain.server, ship, SoundEvents.RAID_HORN.value(), 2f, 0.6f);
        COUNTDOWNS.put(ship.plot, COUNTDOWN);
        return true;
    }

    /** Тик из ShipTicker: отсчёт до разлома, шумы варпа в переходе. */
    static void tick(MinecraftServer server, Ship ship) {
        Integer left = COUNTDOWNS.get(ship.plot);
        if (left != null) {
            left--;
            if (left % 20 == 0 && left > 0) {
                int n = left / 20;
                for (ServerPlayer p : ShipService.crew(server, ship)) {
                    p.displayClientMessage(Component.translatable("flight.warpbound.countdown", n)
                            .withStyle(ChatFormatting.RED, ChatFormatting.BOLD), true);
                }
                sound(server, ship, SoundEvents.NOTE_BLOCK_BASS.value(), 2f, 0.5f + n * 0.1f);
            }
            if (left <= 0) {
                COUNTDOWNS.remove(ship.plot);
                ShipService.startWarp(ship, Math.min(ShipNavigation.CALM_TRANSIT_SECONDS,
                        dev.warpbound.config.WarpboundConfig.get().warpTransitSeconds));
                sound(server, ship, SoundEvents.LIGHTNING_BOLT_THUNDER, 4f, 0.6f);
                sound(server, ship, WarpboundSounds.WARP_BURST, 3f, 0.5f);
                sound(server, ship, WarpboundSounds.WARP_WHISPER, 3f, 0.6f);
                vox(server, ship, "flight.warpbound.vox.translation");
                ShipRegistry.get(server).setDirty();
            } else {
                COUNTDOWNS.put(ship.plot, left);
            }
        }
        // раскрытие и транзит: гром, шёпоты, что-то скребётся по корпусу
        if (ship.state == ShipState.ENTERING && ship.stateTicks % 25 == 0) {
            sound(server, ship, SoundEvents.LIGHTNING_BOLT_THUNDER, 3f, 0.5f + server.overworld().random.nextFloat() * 0.3f);
        }
        if (ship.state == ShipState.TRANSIT) {
            var r = server.overworld().random;
            if (r.nextInt(400) == 0) sound(server, ship, WarpboundSounds.WARP_WHISPER, 2f, 0.6f + r.nextFloat() * 0.3f);
            if (r.nextInt(600) == 0) sound(server, ship, SoundEvents.LIGHTNING_BOLT_THUNDER, 1.5f, 0.4f);
            if (r.nextInt(900) == 0) {
                sound(server, ship, SoundEvents.GRINDSTONE_USE, 1.5f, 0.3f);
                for (ServerPlayer p : ShipService.crew(server, ship)) {
                    p.displayClientMessage(Component.translatable("flight.warpbound.scratching")
                            .withStyle(ChatFormatting.DARK_PURPLE, ChatFormatting.ITALIC), true);
                }
            }
        }
    }

    private static void vox(MinecraftServer server, Ship ship, String key) {
        for (ServerPlayer p : ShipService.crew(server, ship)) {
            p.displayClientMessage(Component.translatable(key).withStyle(ChatFormatting.GOLD), false);
        }
    }

    /** Звук слышен всем на борту, где бы они ни были (корабльная трансляция). */
    private static void sound(MinecraftServer server, Ship ship, SoundEvent event, float volume, float pitch) {
        for (ServerPlayer p : ShipService.crew(server, ship)) {
            p.playNotifySound(event, SoundSource.AMBIENT, volume, pitch);
        }
    }

    public static BlockPos bridge(Ship ship) {
        return ShipInteriors.spawn(ship);
    }
}
