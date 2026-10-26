package dev.warpbound.ship;

import dev.warpbound.Warpbound;
import dev.warpbound.chaos.ChaosLogic;
import dev.warpbound.config.WarpboundConfig;
import net.fabricmc.fabric.api.entity.event.v1.ServerEntityWorldChangeEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.event.player.PlayerBlockBreakEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.TagKey;
import net.minecraft.world.level.block.Block;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;

import java.util.List;

/** Серверный тик кораблей: переходы состояний, Поле Геллера, шёпоты. */
public final class ShipTicker {
    /** Что игрок может ставить и убирать на борту. */
    public static final TagKey<Block> PLAYER_PLACEABLE = TagKey.create(Registries.BLOCK, Warpbound.id("ship_player_placeable"));

    private ShipTicker() {
    }

    public static void register() {
        ServerTickEvents.END_SERVER_TICK.register(ShipTicker::tick);
        ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> ShipService.sync(handler.getPlayer()));
        ServerEntityWorldChangeEvents.AFTER_PLAYER_CHANGE_WORLD.register((player, origin, destination) -> ShipService.sync(player));
        // Интерьер корабля собран из модулей: стены не ломаются, своё (сундуки, верстаки, факелы) — можно
        PlayerBlockBreakEvents.BEFORE.register((level, player, pos, state, be) -> {
            if (!ShipInteriors.isInterior(level) || player.isCreative() || state.is(PLAYER_PLACEABLE)) return true;
            player.displayClientMessage(Component.translatable("ship.warpbound.hull_unbreakable").withStyle(ChatFormatting.GRAY), true);
            return false;
        });
    }

    private static void tick(MinecraftServer server) {
        ShipRegistry registry = ShipRegistry.get(server);
        boolean dirty = false;
        for (Ship ship : registry.all()) {
            ShipSystems.tick(server, ship);
            ShipFlight.tick(server, ship);
            if (server.getTickCount() % 20 == 0) {
                for (ServerPlayer p : ShipService.crew(server, ship)) ServerPlayNetworking.send(p, ShipService.payload(ship));
            }
            if (ship.state == ShipState.ORBIT) {
                // На орбите генератор Поля подзаряжается — тем быстрее, чем больше мощности реактора отдано Полю
                if (ship.field < 1f) {
                    ship.field = Math.min(1f, ship.field + WarpboundConfig.get().fieldRechargePerMinute / 1200f
                            * (0.4f + 1.2f * ShipSystems.fieldSupply(ship)));
                }
                dirty = true;
                continue;
            }
            dirty = true;
            ship.stateTicks += ShipSystems.transitStep(ship);
            boolean changed = false;

            if (ship.state == ShipState.TRANSIT) {
                tickTransit(server, ship);
            }
            if (ship.state != ShipState.ORBIT && ship.stateTicks >= ShipService.durationTicks(ship)) {
                advance(server, ship);
                changed = true;
            }
            if (changed || ship.stateTicks % 20 == 0) {
                for (ServerPlayer p : ShipService.crew(server, ship)) {
                    ServerPlayNetworking.send(p, ShipService.payload(ship));
                }
            }
        }
        if (dirty) registry.setDirty();
    }

    private static void advance(MinecraftServer server, Ship ship) {
        ShipState next = switch (ship.state) {
            case ENTERING -> ShipState.TRANSIT;
            case TRANSIT -> ShipState.EXITING;
            case EXITING, ORBIT -> ShipState.ORBIT;
        };
        ship.state = next;
        ship.stateTicks = 0;
        if (next == ShipState.ORBIT) arrive(server, ship);
        String text = switch (next) {
            case TRANSIT -> "Корабль в варпе. Да хранит нас Император.";
            case EXITING -> "Навигатор ведёт корабль к выходу.";
            case ORBIT -> null; // о прибытии говорит arrive()
            default -> null;
        };
        if (text != null) broadcast(server, ship, Component.literal(text).withStyle(ChatFormatting.GOLD));
    }

    /** Выход на орбиту цели. Аварийный выход бросает корабль к случайному известному миру. */
    private static void arrive(MinecraftServer server, Ship ship) {
        ResourceLocation target = ship.destination;
        if (ship.aborted) {
            var known = ShipDestination.REGISTRY.all().entrySet().stream()
                    .filter(e -> e.getValue().level(server).isPresent()).map(java.util.Map.Entry::getKey).toList();
            if (!known.isEmpty()) target = known.get(server.overworld().random.nextInt(known.size()));
        }
        ship.aborted = false;
        ship.destination = null;
        if (target != null) ship.location = target;
        var name = ShipDestination.REGISTRY.get(ship.location)
                .map(d -> (Component) Component.translatable(d.name())).orElse(Component.literal(ship.location.toString()));
        broadcast(server, ship, Component.translatable("ship.warpbound.arrived", name).withStyle(ChatFormatting.GOLD));
    }

    private static void tickTransit(MinecraftServer server, Ship ship) {
        WarpboundConfig cfg = WarpboundConfig.get();
        // питание от реактора тормозит просадку Поля: без питания оно тает в полтора раза быстрее
        float drain = cfg.fieldDrainPerMinute / 1200f * (1f + ship.storm * (cfg.stormDrainMultiplier - 1f))
                * (1.5f - ShipSystems.fieldSupply(ship));
        ship.field = Math.max(0f, ship.field - drain);

        if (ship.field <= 0f) {
            broadcast(server, ship, Component.literal("Поле Геллера пало! Аварийный выход из варпа!")
                    .withStyle(ChatFormatting.DARK_RED, ChatFormatting.BOLD));
            ShipService.abortWarp(ship);
            ship.aborted = true;
            return;
        }

        // Шёпоты: при слабом Поле экипаж медленно набирает порчу
        int interval = Math.max(1, cfg.whisperIntervalSeconds) * 20;
        if (ship.field < cfg.whisperFieldThreshold && ship.stateTicks % interval == 0) {
            float weakness = 1f - ship.field / cfg.whisperFieldThreshold;
            float amount = cfg.whisperCorruption * weakness;
            List<ServerPlayer> crew = ShipService.crew(server, ship);
            for (ServerPlayer p : crew) {
                p.displayClientMessage(Component.literal("Шёпоты варпа просачиваются сквозь Поле...")
                        .withStyle(ChatFormatting.DARK_PURPLE, ChatFormatting.ITALIC), true);
                ChaosLogic.addCorruption(p, amount);
            }
        }
    }

    private static void broadcast(MinecraftServer server, Ship ship, Component message) {
        for (ServerPlayer p : ShipService.crew(server, ship)) p.displayClientMessage(message, false);
    }
}
