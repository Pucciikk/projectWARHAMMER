package dev.warpbound.ship;

import dev.warpbound.network.ShipConsoleActionPayload;
import dev.warpbound.network.ShipConsolePayload;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;

import dev.warpbound.multiblock.Multiblocks;
import dev.warpbound.shipyard.ShipyardBlockEntity;
import net.minecraft.core.BlockPos;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;

/** Командный пульт мостика: открыть экран, обновлять его, выполнять команды экипажа. */
public final class ShipConsole {
    private ShipConsole() {
    }

    public static void register() {
        ServerPlayNetworking.registerGlobalReceiver(ShipConsoleActionPayload.TYPE,
                (payload, context) -> handle(context.player(), payload));
    }

    /** У какого пульта стоит игрок — нужен, пока корабль на стапеле (пульт — часть постройки в доке). */
    private static final Map<UUID, BlockPos> LAST_CONSOLE = new HashMap<>();

    /** ПКМ по пульту (в космосе — корабль игрока, у причала — корабль на стапеле). */
    public static void open(ServerPlayer player) {
        open(player, null);
    }

    public static void open(ServerPlayer player, BlockPos consolePos) {
        Ship ship = ShipService.shipAboard(player).orElse(null);
        if (ship == null && consolePos != null) {
            ShipyardBlockEntity yard = dockOf(player, consolePos);
            if (yard != null) {
                LAST_CONSOLE.put(player.getUUID(), consolePos.immutable());
                ServerPlayNetworking.send(player, docked(yard, true));
                return;
            }
        }
        if (ship == null || !ShipNavigation.isCrew(player, ship)) {
            player.displayClientMessage(Component.translatable("ship.warpbound.not_your_ship").withStyle(ChatFormatting.RED), true);
            return;
        }
        ServerPlayNetworking.send(player, snapshot(player, ship, true));
    }

    private static ShipyardBlockEntity dockOf(ServerPlayer player, BlockPos consolePos) {
        return Multiblocks.coreOf(player.level(), consolePos)
                .map(core -> player.level().getBlockEntity(core))
                .filter(be -> be instanceof ShipyardBlockEntity).map(be -> (ShipyardBlockEntity) be).orElse(null);
    }

    private static ShipConsolePayload docked(ShipyardBlockEntity yard, boolean open) {
        return new ShipConsolePayload(open, "", 0, 0, 1, 0, 1, 0.3f, 0.75f, 0.75f, 0, 0, 0, 0, "", "", List.of(), List.of(),
                true, yard.stage(), yard.stageCount(), yard.isLaunching(), 0, yard.isComplete() ? "" : "flight.warpbound.need.built");
    }

    private static void handle(ServerPlayer player, ShipConsoleActionPayload action) {
        Ship ship = ShipService.shipAboard(player).orElse(null);
        if (ship == null) {
            // корабль ещё в доке: только обновление и выход в космос
            BlockPos pos = LAST_CONSOLE.get(player.getUUID());
            ShipyardBlockEntity yard = pos == null ? null : dockOf(player, pos);
            if (yard == null) return;
            if (action.action() == ShipConsoleActionPayload.LAUNCH && yard.isComplete()) yard.launch(player);
            ServerPlayNetworking.send(player, docked(yard, false));
            return;
        }
        if (!ShipNavigation.isCrew(player, ship)) return;
        boolean changed = switch (action.action()) {
            case ShipConsoleActionPayload.ENGINES -> ShipFlight.toggleEngines(player, ship);
            case ShipConsoleActionPayload.GELLER -> ShipFlight.toggleGeller(player, ship);
            case ShipConsoleActionPayload.SHUTTERS -> ShipFlight.toggleShutters(player, ship);
            case ShipConsoleActionPayload.OPEN_RIFT -> ShipFlight.openRift(player, ship);
            case ShipConsoleActionPayload.REACTOR_MODE -> ShipSystems.setReactorMode(ship, (int) action.value());
            case ShipConsoleActionPayload.GELLER_POWER -> ShipSystems.setGellerPower(ship, action.value());
            case ShipConsoleActionPayload.FIELD_BOOST -> ShipSystems.boostField(player.serverLevel(), ship);
            case ShipConsoleActionPayload.COOLANT_FLUSH -> ShipSystems.flushCoolant(player.serverLevel(), ship);
            case ShipConsoleActionPayload.PLOT_COURSE -> {
                ResourceLocation target = ResourceLocation.tryParse(action.target());
                if (target != null) ShipNavigation.jump(player, target);
                yield true;
            }
            default -> false;
        };
        if (changed) ShipRegistry.get(player.server).setDirty();
        ServerPlayNetworking.send(player, snapshot(player, ship, false));
    }

    private static ShipConsolePayload snapshot(ServerPlayer player, Ship ship, boolean open) {
        List<String> ids = new ArrayList<>(), names = new ArrayList<>();
        for (var e : ShipDestination.REGISTRY.all().entrySet()) {
            if (e.getValue().level(player.server).isEmpty()) continue;
            ids.add(e.getKey().toString());
            names.add(e.getValue().name());
        }
        var mode = ShipSystems.ReactorMode.of(ship);
        float progress = Math.min(1f, ship.stateTicks / (float) ShipService.durationTicks(ship));
        return new ShipConsolePayload(open, ship.name, ship.state.ordinal(), progress, ship.field, ship.storm,
                mode.ordinal(), ship.heat, mode.power, ship.gellerPower, ship.radiation, ship.boostCooldown, ship.flushCooldown,
                ShipService.crew(player.server, ship).size(), ship.location.toString(),
                ship.destination == null ? "" : ship.destination.toString(), ids, names,
                false, 0, 0, false, (ship.enginesOn ? 1 : 0) | (ship.gellerOn ? 2 : 0) | (ship.shuttersClosed ? 4 : 0),
                Objects.requireNonNullElse(ShipFlight.missing(ship), ""));
    }
}
