package dev.warpbound.team;

import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;

import java.util.Optional;
import java.util.UUID;
import java.util.stream.Collectors;

/** /warband — отряды. Доступно всем игрокам, без прав оператора. */
public final class TeamCommands {
    private TeamCommands() {
    }

    public static void register() {
        CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
                Commands.literal("warband")
                        .then(Commands.literal("create")
                                .then(Commands.argument("name", StringArgumentType.greedyString()).executes(ctx -> {
                                    ServerPlayer p = ctx.getSource().getPlayerOrException();
                                    Team team = TeamRegistry.get(p.server).create(p.getUUID(), StringArgumentType.getString(ctx, "name"));
                                    return ok(ctx, "Отряд «" + team.name + "» создан. Ты его лидер.");
                                })))
                        .then(Commands.literal("invite")
                                .then(Commands.argument("player", EntityArgument.player()).executes(ctx -> {
                                    ServerPlayer p = ctx.getSource().getPlayerOrException();
                                    ServerPlayer target = EntityArgument.getPlayer(ctx, "player");
                                    TeamRegistry registry = TeamRegistry.get(p.server);
                                    Team team = registry.of(p.getUUID(), p.getGameProfile().getName() + " и спутники");
                                    if (!team.leader.equals(p.getUUID())) return fail(ctx, "Приглашать может только лидер отряда.");
                                    registry.invite(team, target.getUUID());
                                    target.sendSystemMessage(Component.literal(p.getGameProfile().getName()
                                            + " зовёт тебя в отряд «" + team.name + "». Принять: /warband accept").withStyle(ChatFormatting.GOLD));
                                    return ok(ctx, "Приглашение отправлено.");
                                })))
                        .then(Commands.literal("accept").executes(ctx -> {
                            ServerPlayer p = ctx.getSource().getPlayerOrException();
                            Optional<Team> team = TeamRegistry.get(p.server).accept(p.getUUID());
                            if (team.isEmpty()) return fail(ctx, "Приглашений нет.");
                            return ok(ctx, "Ты вступил в отряд «" + team.get().name + "».");
                        }))
                        .then(Commands.literal("leave").executes(ctx -> {
                            ServerPlayer p = ctx.getSource().getPlayerOrException();
                            TeamRegistry.get(p.server).leave(p.getUUID());
                            return ok(ctx, "Ты покинул отряд. Свои исследования ты сохранишь.");
                        }))
                        .then(Commands.literal("info").executes(TeamCommands::info))));
    }

    private static int info(CommandContext<CommandSourceStack> ctx) throws CommandSyntaxException {
        ServerPlayer p = ctx.getSource().getPlayerOrException();
        Optional<Team> team = TeamRegistry.get(p.server).find(p.getUUID());
        if (team.isEmpty() || team.get().solo()) return ok(ctx, "Ты странствуешь один.");
        String members = team.get().members.stream().map(id -> name(p, id)).collect(Collectors.joining(", "));
        return ok(ctx, "Отряд «" + team.get().name + "», лидер " + name(p, team.get().leader) + ". Состав: " + members);
    }

    private static String name(ServerPlayer p, UUID id) {
        ServerPlayer online = p.server.getPlayerList().getPlayer(id);
        if (online != null) return online.getGameProfile().getName();
        return p.server.getProfileCache() == null ? id.toString()
                : p.server.getProfileCache().get(id).map(com.mojang.authlib.GameProfile::getName).orElse(id.toString());
    }

    private static int ok(CommandContext<CommandSourceStack> ctx, String text) {
        ctx.getSource().sendSuccess(() -> Component.literal(text), false);
        return 1;
    }

    private static int fail(CommandContext<CommandSourceStack> ctx, String text) {
        ctx.getSource().sendFailure(Component.literal(text));
        return 0;
    }
}
