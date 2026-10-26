package dev.warpbound.operator;

import dev.warpbound.chaos.ChaosLogic;
import dev.warpbound.core.WarpboundItems;
import dev.warpbound.entity.WarpboundEntities;
import dev.warpbound.entity.ritual.WarpRiftEntity;
import dev.warpbound.entity.transport.ShuttleEntity;
import dev.warpbound.quest.QuestManager;
import dev.warpbound.quest.StoryFlags;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitlesAnimationPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.levelgen.Heightmap;

/**
 * Прибытие первого оператора по Знаку Омниссии.
 * Империум: прилетает челнок, садится (или зависает над неровной землёй) и сбрасывает капсулу с техножрецом.
 * Хаос: ритуал синего варп-пламени, тёмный техножрец поднимается из-под земли; игрок получает немного порчи.
 * Глава закрывается, когда оператор ступил на землю ({@link #landed}).
 */
public final class OperatorArrival {
    /** Челнок большой: садится дальше от маяка, чем открывается разлом. */
    private static final int SHUTTLE_OFFSET = 10, RITUAL_OFFSET = 5;
    private static final float DESECRATION_CORRUPTION = 5f;

    private OperatorArrival() {
    }

    public static void callShuttle(ServerLevel level, BlockPos beacon, ServerPlayer player) {
        BlockPos ground = landingSpot(level, beacon, SHUTTLE_OFFSET);
        ShuttleEntity.dispatch(level, ground, WarpboundEntities.TECH_PRIEST, player.getUUID());

        level.playSound(null, beacon, SoundEvents.BEACON_POWER_SELECT, SoundSource.BLOCKS, 1f, 0.7f);
        player.displayClientMessage(Component.literal("+++ ВОКС: Сигнал принят. Челнок Механикус заходит на посадку. +++")
                .withStyle(ChatFormatting.RED), false);
        QuestManager.setFlag(player, StoryFlags.PATH_MECHANICUS);
        give(player, new ItemStack(WarpboundItems.FORGE_SCHEMATIC));
    }

    public static void desecrate(ServerLevel level, BlockPos beacon, ServerPlayer player) {
        BlockPos ground = landingSpot(level, beacon, RITUAL_OFFSET);
        WarpRiftEntity.open(level, ground, player.getUUID());
        level.playSound(null, beacon, SoundEvents.ENDERMAN_TELEPORT, SoundSource.HOSTILE, 1.2f, 0.5f);

        ChaosLogic.addCorruption(player, DESECRATION_CORRUPTION);
        player.displayClientMessage(Component.literal("Знак чернеет в руке. Земля вспыхивает синим огнём — на зов идёт тот, кто служит иному богу машин.")
                .withStyle(ChatFormatting.DARK_PURPLE, ChatFormatting.ITALIC), false);
        QuestManager.setFlag(player, StoryFlags.PATH_DARK_MECHANICUM);
        give(player, new ItemStack(WarpboundItems.OBELISK_SCHEMATIC));
    }

    /** Техножрец коснулся земли. */
    static void landed(TechPriestEntity priest) {
        priest.owner().map(id -> priest.getServer().getPlayerList().getPlayer(id)).ifPresent(OperatorArrival::finishChapter);
    }

    private static void finishChapter(ServerPlayer player) {
        QuestManager.setFlag(player, StoryFlags.OPERATOR_ARRIVED);
        player.connection.send(new ClientboundSetTitlesAnimationPacket(15, 80, 25));
        player.connection.send(new ClientboundSetSubtitleTextPacket(Component.literal("Обломки").withStyle(ChatFormatting.GRAY)));
        player.connection.send(new ClientboundSetTitleTextPacket(Component.literal("ГЛАВА I ЗАВЕРШЕНА").withStyle(ChatFormatting.GOLD)));
        player.playNotifySound(SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, SoundSource.MASTER, 1f, 0.8f);
    }

    /** Рядом с маяком, на поверхности, в стороне от капсулы и обломков. */
    private static BlockPos landingSpot(ServerLevel level, BlockPos beacon, int offset) {
        BlockPos side = beacon.offset(0, 0, offset);
        return level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, side);
    }

    private static void give(ServerPlayer player, ItemStack stack) {
        if (!player.getInventory().add(stack)) player.drop(stack, false);
    }
}
