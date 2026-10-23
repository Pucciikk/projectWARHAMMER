package dev.warpbound.client.quest;

import dev.warpbound.quest.QuestDef;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.toasts.Toast;
import net.minecraft.client.gui.components.toasts.ToastComponent;
import net.minecraft.client.resources.sounds.SimpleSoundInstance;
import net.minecraft.sounds.SoundEvents;

/** Уведомление «Квест выполнен» в стиле окна квестов. */
public class QuestToast implements Toast {
    private static final long SHOW_MS = 5000;
    private final QuestDef quest;
    private boolean playedSound;

    public QuestToast(QuestDef quest) {
        this.quest = quest;
    }

    @Override
    public Visibility render(GuiGraphics g, ToastComponent toasts, long time) {
        if (!playedSound) {
            playedSound = true;
            toasts.getMinecraft().getSoundManager().play(SimpleSoundInstance.forUI(SoundEvents.BELL_RESONATE, 1.4f, 0.6f));
        }
        int w = width(), h = height();
        g.fill(0, 0, w, h, 0xF0140E0C);
        g.renderOutline(0, 0, w, h, 0xFF8A6A2A);
        g.fill(1, 1, w - 1, 2, 0xFF7A1212);
        g.blit(ClientQuestState.iconTexture(quest.icon()), 7, 8, 16, 16, 0, 0, 32, 32, 32, 32);
        g.drawString(toasts.getMinecraft().font, "Квест выполнен", 30, 7, 0xFFC9A227, false);
        g.drawString(toasts.getMinecraft().font, quest.title(), 30, 18, 0xFFE8E0D0, false);
        return time >= SHOW_MS * toasts.getNotificationDisplayTimeMultiplier() ? Visibility.HIDE : Visibility.SHOW;
    }
}
