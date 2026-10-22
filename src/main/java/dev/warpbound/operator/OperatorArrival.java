package dev.warpbound.operator;

import dev.warpbound.chaos.ChaosLogic;
import dev.warpbound.core.WarpboundItems;
import dev.warpbound.entity.WarpboundEntities;
import dev.warpbound.quest.QuestManager;
import dev.warpbound.quest.StoryFlags;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitlesAnimationPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.levelgen.Heightmap;

/**
 * Прибытие первого оператора по Знаку Омниссии.
 * Империум: техножрец спускается с неба с дымом и огнём (настоящий челнок — с операторами на этапе 3).
 * Хаос: тёмный техножрец выходит из синей варп-вспышки, игрок получает немного порчи.
 */
public final class OperatorArrival {
    private static final int DROP_HEIGHT = 28;
    private static final float DESECRATION_CORRUPTION = 5f;

    private OperatorArrival() {
    }

    public static void callShuttle(ServerLevel level, BlockPos beacon, ServerPlayer player) {
        BlockPos ground = landingSpot(level, beacon);
        TechPriestEntity priest = WarpboundEntities.TECH_PRIEST.create(level);
        if (priest == null) return;
        priest.moveTo(ground.getX() + 0.5, ground.getY() + DROP_HEIGHT, ground.getZ() + 0.5, level.random.nextFloat() * 360f, 0f);
        priest.setOwner(player.getUUID());
        priest.finalizeSpawn(level, level.getCurrentDifficultyAt(ground), MobSpawnType.EVENT, null);
        priest.startDescent();
        level.addFreshEntity(priest);

        level.playSound(null, beacon, SoundEvents.BEACON_POWER_SELECT, SoundSource.BLOCKS, 1f, 0.7f);
        player.displayClientMessage(Component.literal("+++ ВОКС: Сигнал принят. Слуга Омниссии нисходит. +++")
                .withStyle(ChatFormatting.RED), false);
        QuestManager.setFlag(player, StoryFlags.PATH_MECHANICUS);
        give(player, new ItemStack(WarpboundItems.FORGE_SCHEMATIC));
    }

    public static void desecrate(ServerLevel level, BlockPos beacon, ServerPlayer player) {
        BlockPos ground = landingSpot(level, beacon);
        double x = ground.getX() + 0.5, y = ground.getY(), z = ground.getZ() + 0.5;
        level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, x, y + 1, z, 120, 0.6, 1.0, 0.6, 0.08);
        level.sendParticles(ParticleTypes.REVERSE_PORTAL, x, y + 1, z, 80, 0.5, 1.0, 0.5, 0.3);
        level.sendParticles(ParticleTypes.FLASH, x, y + 1, z, 1, 0, 0, 0, 0);
        level.playSound(null, ground, SoundEvents.ENDERMAN_TELEPORT, SoundSource.HOSTILE, 1.2f, 0.5f);
        level.playSound(null, ground, SoundEvents.WITHER_AMBIENT, SoundSource.HOSTILE, 0.5f, 0.6f);

        TechPriestEntity priest = WarpboundEntities.DARK_TECH_PRIEST.create(level);
        if (priest == null) return;
        priest.moveTo(x, y, z, level.random.nextFloat() * 360f, 0f);
        priest.setOwner(player.getUUID());
        priest.finalizeSpawn(level, level.getCurrentDifficultyAt(ground), MobSpawnType.EVENT, null);
        level.addFreshEntity(priest);

        ChaosLogic.addCorruption(player, DESECRATION_CORRUPTION);
        player.displayClientMessage(Component.literal("Знак чернеет в руке. Из пламени выходит тот, кто служит иному богу машин.")
                .withStyle(ChatFormatting.DARK_PURPLE, ChatFormatting.ITALIC), false);
        QuestManager.setFlag(player, StoryFlags.PATH_DARK_MECHANICUM);
        give(player, new ItemStack(WarpboundItems.OBELISK_SCHEMATIC));
        finishChapter(player);
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

    /** Рядом с маяком, на поверхности, чтобы не приземлиться в капсулу. */
    private static BlockPos landingSpot(ServerLevel level, BlockPos beacon) {
        BlockPos side = beacon.offset(0, 0, 5);
        return level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, side);
    }

    private static void give(ServerPlayer player, ItemStack stack) {
        if (!player.getInventory().add(stack)) player.drop(stack, false);
    }
}
