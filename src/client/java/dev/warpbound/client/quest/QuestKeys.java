package dev.warpbound.client.quest;

import com.mojang.blaze3d.platform.InputConstants;
import dev.warpbound.Warpbound;
import dev.warpbound.client.mixin.AbstractContainerScreenAccessor;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keybinding.v1.KeyBindingHelper;
import net.fabricmc.fabric.api.client.screen.v1.ScreenEvents;
import net.fabricmc.fabric.api.client.screen.v1.Screens;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.Tooltip;
import net.minecraft.client.gui.screens.inventory.InventoryScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import org.lwjgl.glfw.GLFW;

/** Хоткей J и кнопка с аквилой над инвентарём: оба открывают журнал памяти. */
public final class QuestKeys {
    public static final KeyMapping OPEN = KeyBindingHelper.registerKeyBinding(new KeyMapping(
            "key.warpbound.quests", InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_J, "key.categories.warpbound"));

    private static final ResourceLocation BUTTON = Warpbound.id("textures/gui/quest/button.png");

    private QuestKeys() {
    }

    public static void register() {
        ClientTickEvents.END_CLIENT_TICK.register(mc -> {
            while (OPEN.consumeClick()) {
                if (mc.screen == null && mc.player != null) mc.setScreen(new QuestScreen());
            }
        });

        ScreenEvents.AFTER_INIT.register((client, screen, scaledWidth, scaledHeight) -> {
            if (!(screen instanceof InventoryScreen inventory)) return;
            AquilaButton button = new AquilaButton(() -> client.setScreen(new QuestScreen()));
            Screens.getButtons(screen).add(button);
            // окно сдвигается, когда открывают книгу рецептов: кнопка едет следом каждый кадр
            ScreenEvents.beforeRender(screen).register((s, g, mouseX, mouseY, delta) -> {
                AbstractContainerScreenAccessor acc = (AbstractContainerScreenAccessor) inventory;
                button.setPosition(acc.warpbound$leftPos() + 176 - 22, acc.warpbound$topPos() - 19);
            });
        });
    }

    private static class AquilaButton extends Button {
        AquilaButton(Runnable onPress) {
            super(0, 0, 20, 18, Component.literal("Журнал памяти"), b -> onPress.run(), DEFAULT_NARRATION);
            setTooltip(Tooltip.create(Component.literal("Журнал памяти (")
                    .append(OPEN.getTranslatedKeyMessage()).append(")")));
        }

        @Override
        protected void renderWidget(GuiGraphics g, int mouseX, int mouseY, float partialTick) {
            g.blit(BUTTON, getX(), getY(), 0, isHoveredOrFocused() ? 18 : 0, 20, 18, 20, 36);
        }
    }
}
