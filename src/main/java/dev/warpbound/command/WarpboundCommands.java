package dev.warpbound.command;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.FloatArgumentType;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import com.mojang.brigadier.exceptions.SimpleCommandExceptionType;
import dev.warpbound.chaos.ChaosData;
import dev.warpbound.chaos.ChaosGod;
import dev.warpbound.chaos.ChaosLogic;
import dev.warpbound.config.WarpboundConfig;
import dev.warpbound.quest.QuestManager;
import dev.warpbound.start.CrashSite;
import dev.warpbound.ship.Ship;
import dev.warpbound.ship.ShipRegistry;
import dev.warpbound.ship.ShipService;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;

import java.util.Locale;
import java.util.Optional;

/**
 * Отладочные команды /wb. Нужны права оператора (в одиночной игре — «Разрешить читы»).
 */
public final class WarpboundCommands {
    private static final SimpleCommandExceptionType NOT_ABOARD =
            new SimpleCommandExceptionType(Component.literal("Ты не на борту корабля. Сначала /wb ship enter."));

    private WarpboundCommands() {
    }

    public static void register() {
        CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> register(dispatcher));
    }

    private static void register(CommandDispatcher<CommandSourceStack> dispatcher) {
        dispatcher.register(Commands.literal("wb")
                .requires(source -> source.hasPermission(2))
                .then(Commands.literal("chaos")
                        .then(Commands.literal("get").executes(WarpboundCommands::chaosGet))
                        .then(Commands.literal("add")
                                .then(Commands.argument("amount", FloatArgumentType.floatArg(-100, 100))
                                        .executes(ctx -> {
                                            ServerPlayer p = ctx.getSource().getPlayerOrException();
                                            ChaosLogic.addCorruption(p, FloatArgumentType.getFloat(ctx, "amount"));
                                            return chaosGet(ctx);
                                        })))
                        .then(Commands.literal("set")
                                .then(Commands.argument("field", StringArgumentType.word())
                                        .suggests((ctx, builder) -> {
                                            for (String s : new String[]{"corruption", "taint", "disappointment", "khorne", "nurgle", "tzeentch", "slaanesh"}) builder.suggest(s);
                                            return builder.buildFuture();
                                        })
                                        .then(Commands.argument("value", FloatArgumentType.floatArg(0, 100))
                                                .executes(WarpboundCommands::chaosSet))))
                        .then(Commands.literal("reset").executes(ctx -> {
                            ChaosLogic.set(ctx.getSource().getPlayerOrException(), ChaosData.EMPTY);
                            return chaosGet(ctx);
                        })))
                .then(Commands.literal("ship")
                        .then(Commands.literal("create")
                                .executes(ctx -> shipCreate(ctx, "Безымянный"))
                                .then(Commands.argument("name", StringArgumentType.greedyString())
                                        .executes(ctx -> shipCreate(ctx, StringArgumentType.getString(ctx, "name")))))
                        .then(Commands.literal("enter").executes(ctx -> {
                            ServerPlayer p = ctx.getSource().getPlayerOrException();
                            Ship ship = ShipService.createFor(p, "Безымянный");
                            ShipService.enter(p, ship);
                            return 1;
                        }))
                        .then(Commands.literal("leave").executes(ctx -> {
                            ServerPlayer p = ctx.getSource().getPlayerOrException();
                            Optional<Ship> ship = ShipService.shipAboard(p);
                            if (ship.isEmpty()) return fail(ctx, "Ты не на борту корабля.");
                            if (!ShipService.leave(p, ship.get())) return fail(ctx, "Во время варп-перехода выйти нельзя.");
                            return 1;
                        }))
                        .then(Commands.literal("warp")
                                .executes(ctx -> shipWarp(ctx, WarpboundConfig.get().warpTransitSeconds))
                                .then(Commands.argument("seconds", IntegerArgumentType.integer(5, 7200))
                                        .executes(ctx -> shipWarp(ctx, IntegerArgumentType.getInteger(ctx, "seconds")))))
                        .then(Commands.literal("abort").executes(ctx -> {
                            Ship ship = aboard(ctx);
                            if (!ShipService.abortWarp(ship)) return fail(ctx, "Корабль сейчас не в варпе.");
                            ok(ctx, "Аварийный выход из варпа!");
                            return 1;
                        }))
                        .then(Commands.literal("field")
                                .then(Commands.argument("percent", FloatArgumentType.floatArg(0, 100)).executes(ctx -> {
                                    Ship ship = aboard(ctx);
                                    ship.field = FloatArgumentType.getFloat(ctx, "percent") / 100f;
                                    touched(ctx, ship);
                                    return shipInfo(ctx);
                                })))
                        .then(Commands.literal("storm")
                                .then(Commands.argument("percent", FloatArgumentType.floatArg(0, 100)).executes(ctx -> {
                                    Ship ship = aboard(ctx);
                                    ship.storm = FloatArgumentType.getFloat(ctx, "percent") / 100f;
                                    touched(ctx, ship);
                                    return shipInfo(ctx);
                                })))
                        .then(Commands.literal("info").executes(WarpboundCommands::shipInfo)))
                .then(Commands.literal("crashsite").executes(ctx -> {
                    ServerPlayer p = ctx.getSource().getPlayerOrException();
                    CrashSite.place(p.serverLevel(), p.blockPosition(), p.getRandom());
                    ok(ctx, "Место крушения поставлено рядом.");
                    return 1;
                }))
                .then(Commands.literal("quest")
                        .then(Commands.literal("reset").executes(ctx -> {
                            QuestManager.reset(ctx.getSource().getPlayerOrException());
                            ok(ctx, "Прогресс квестов и сюжетные флаги сброшены.");
                            return 1;
                        }))
                        .then(Commands.literal("flag")
                                .then(Commands.argument("flag", StringArgumentType.word()).executes(ctx -> {
                                    QuestManager.setFlag(ctx.getSource().getPlayerOrException(), StringArgumentType.getString(ctx, "flag"));
                                    ok(ctx, "Флаг поставлен.");
                                    return 1;
                                })))));
    }

    // --- Хаос ---

    private static int chaosGet(CommandContext<CommandSourceStack> ctx) throws CommandSyntaxException {
        ChaosData d = ChaosLogic.get(ctx.getSource().getPlayerOrException());
        StringBuilder favor = new StringBuilder();
        for (ChaosGod god : ChaosGod.values()) {
            favor.append(god.displayName).append(' ').append(fmt(d.favor(god))).append("  ");
        }
        ok(ctx, "Порча " + fmt(d.corruption()) + " (" + d.stage().displayName + "), скверна " + fmt(d.taint())
                + ", разочарование " + fmt(d.disappointment()) + ", возвышение: " + d.ascension());
        ok(ctx, "Благосклонность: " + favor.toString().trim());
        return 1;
    }

    private static int chaosSet(CommandContext<CommandSourceStack> ctx) throws CommandSyntaxException {
        ServerPlayer p = ctx.getSource().getPlayerOrException();
        String field = StringArgumentType.getString(ctx, "field").toLowerCase(Locale.ROOT);
        float value = FloatArgumentType.getFloat(ctx, "value");
        ChaosData d = ChaosLogic.get(p);
        switch (field) {
            case "corruption" -> ChaosLogic.setCorruption(p, value);
            case "taint" -> ChaosLogic.set(p, d.withTaint(value));
            case "disappointment" -> ChaosLogic.set(p, d.withDisappointment(value));
            default -> {
                ChaosGod god;
                try {
                    god = ChaosGod.valueOf(field.toUpperCase(Locale.ROOT));
                } catch (IllegalArgumentException e) {
                    return fail(ctx, "Неизвестное поле: " + field);
                }
                ChaosLogic.set(p, d.withFavor(god, value));
            }
        }
        return chaosGet(ctx);
    }

    // --- Корабль ---

    private static int shipCreate(CommandContext<CommandSourceStack> ctx, String name) throws CommandSyntaxException {
        ServerPlayer p = ctx.getSource().getPlayerOrException();
        boolean had = ShipRegistry.get(p.server).ownedBy(p.getUUID()).isPresent();
        Ship ship = ShipService.createFor(p, name);
        ok(ctx, had ? "У тебя уже есть корабль «" + ship.name + "». /wb ship enter — подняться на борт."
                : "Заложен корабль «" + ship.name + "». /wb ship enter — подняться на борт.");
        return 1;
    }

    private static int shipWarp(CommandContext<CommandSourceStack> ctx, int seconds) throws CommandSyntaxException {
        Ship ship = aboard(ctx);
        if (!ShipService.startWarp(ship, seconds)) return fail(ctx, "Корабль уже в варпе.");
        touched(ctx, ship);
        ok(ctx, "Варп-двигатель запущен. Транзит: " + seconds + " с. Поле Геллера: " + Math.round(ship.field * 100) + "%.");
        return 1;
    }

    private static int shipInfo(CommandContext<CommandSourceStack> ctx) throws CommandSyntaxException {
        Ship ship = aboard(ctx);
        int total = ShipService.durationTicks(ship);
        ok(ctx, "«" + ship.name + "»: " + ship.state.displayName
                + (ship.state.ordinal() > 0 ? " (" + ship.stateTicks / 20 + " из " + total / 20 + " с)" : "")
                + ", Поле " + Math.round(ship.field * 100) + "%, шторм " + Math.round(ship.storm * 100) + "%");
        return 1;
    }

    private static Ship aboard(CommandContext<CommandSourceStack> ctx) throws CommandSyntaxException {
        ServerPlayer p = ctx.getSource().getPlayerOrException();
        return ShipService.shipAboard(p).orElseThrow(NOT_ABOARD::create);
    }

    private static void touched(CommandContext<CommandSourceStack> ctx, Ship ship) throws CommandSyntaxException {
        ServerPlayer p = ctx.getSource().getPlayerOrException();
        ShipRegistry.get(p.server).setDirty();
        for (ServerPlayer crew : ShipService.crew(p.server, ship)) ShipService.sync(crew);
    }

    private static String fmt(float v) {
        return String.format(Locale.ROOT, "%.1f", v);
    }

    private static void ok(CommandContext<CommandSourceStack> ctx, String text) {
        ctx.getSource().sendSuccess(() -> Component.literal(text), false);
    }

    private static int fail(CommandContext<CommandSourceStack> ctx, String text) {
        ctx.getSource().sendFailure(Component.literal(text));
        return 0;
    }
}
