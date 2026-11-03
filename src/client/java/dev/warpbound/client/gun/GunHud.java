package dev.warpbound.client.gun;

import dev.warpbound.gun.GunItem;
import net.fabricmc.fabric.api.client.rendering.v1.HudRenderCallback;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

/** Прицел, метка попадания и счётчик патронов. Ванильный прицел отключён, пока в руках оружие. */
public final class GunHud {
    private static final int BRASS = 0xFFD8AE56, BRASS_D = 0xFF7A5A20, PANEL = 0xC018191D, RED = 0xFFE8452E, GREEN = 0xFF66E08A, WHITE = 0xFFE8E8E8;

    private GunHud() {
    }

    public static void register() {
        HudRenderCallback.EVENT.register((g, tick) -> {
            Minecraft mc = Minecraft.getInstance();
            if (mc.player == null || mc.options.hideGui || !(mc.player.getMainHandItem().getItem() instanceof GunItem gun)) return;
            ItemStack stack = mc.player.getMainHandItem();
            if (mc.options.getCameraType().isFirstPerson()) crosshair(g, mc);
            ammo(g, mc, gun, stack);
        });
    }

    private static void crosshair(GuiGraphics g, Minecraft mc) {
        int cx = g.guiWidth() / 2, cy = g.guiHeight() / 2;
        float aim = GunClient.aim;
        // прицел расходится от стрельбы и при ходьбе; в прицеливании его заменяет мушка
        if (aim < 0.6f && !GunClient.reloading()) {
            int alpha = (int) (230 * (1 - aim / 0.6f));
            int c = alpha << 24 | 0xF0F0F0;
            boolean moving = mc.player.getDeltaMovement().horizontalDistanceSqr() > 0.002;
            int gap = 3 + (moving ? 3 : 0) + Math.round(GunClient.bloom * 8);
            int len = 4;
            g.fill(cx - gap - len, cy, cx - gap, cy + 1, c);
            g.fill(cx + gap + 1, cy, cx + gap + 1 + len, cy + 1, c);
            g.fill(cx, cy - gap - len, cx + 1, cy - gap, c);
            g.fill(cx, cy + gap + 1, cx + 1, cy + gap + 1 + len, c);
            g.fill(cx, cy, cx + 1, cy + 1, c);
        }
        // ---- метка попадания: косой крест, красный при убийстве
        double since = GunClient.now(mc) - GunClient.hitAt;
        if (since < 6) {
            int a = (int) (255 * (1 - since / 6));
            int color = a << 24 | (GunClient.hitKilled ? 0xFF3020 : GunClient.hitHead ? 0xFFD040 : 0xFFFFFF);
            int off = GunClient.hitKilled ? 5 : 4;
            for (int i = 0; i < 4; i++) {
                g.fill(cx - off - i, cy - off - i, cx - off - i + 1, cy - off - i + 1, color);
                g.fill(cx + off + i, cy - off - i, cx + off + i + 1, cy - off - i + 1, color);
                g.fill(cx - off - i, cy + off + i, cx - off - i + 1, cy + off + i + 1, color);
                g.fill(cx + off + i, cy + off + i, cx + off + i + 1, cy + off + i + 1, color);
            }
        }
    }

    private static void ammo(GuiGraphics g, Minecraft mc, GunItem gun, ItemStack stack) {
        Font font = mc.font;
        int w = g.guiWidth(), h = g.guiHeight();
        int pw = 78, ph = 30;
        int x = w - pw - 10, y = h - ph - 10;
        g.fill(x - 2, y - 2, x + pw + 2, y + ph + 2, BRASS_D);
        g.fill(x - 1, y - 1, x + pw + 1, y + ph + 1, BRASS);
        g.fill(x, y, x + pw, y + ph, 0xF0141518);
        g.fill(x + 1, y + 1, x + pw - 1, y + ph - 1, PANEL);

        int shown = GunClient.shownAmmo(stack), max = gun.mechanics.magSize();
        boolean low = shown * 4 <= max;
        String count = String.valueOf(shown);
        g.pose().pushPose();
        g.pose().translate(x + 6, y + 5, 0);
        g.pose().scale(2f, 2f, 1f);
        g.drawString(font, count, 0, 0, shown == 0 ? RED : low ? 0xFFE8B84A : WHITE, true);
        g.pose().popPose();
        int tx = x + 8 + font.width(count) * 2;
        g.drawString(font, "/" + max, tx, y + 12, 0xFF9A9A9A, false);
        // запас: сколько магазинов или лазпакетов в инвентаре
        Item ammoItem = gun.ammoItem();
        int mags = mc.player.getAbilities().instabuild ? 99 : mc.player.getInventory().countItem(ammoItem);
        g.renderItem(new ItemStack(ammoItem), x + pw - 22, y + 1);
        String left = "x" + mags;
        g.drawString(font, left, x + pw - 3 - font.width(left), y + 18, mags == 0 ? RED : BRASS, true);
        // полоска патронов снизу: разбита на доли, чтобы остаток читался боковым зрением
        int bx = x + 5, by = y + ph - 5, bw = pw - 10;
        g.fill(bx, by, bx + bw, by + 2, 0xFF2A2A2E);
        int filled = Math.round((float) bw * shown / max);
        g.fill(bx, by, bx + filled, by + 2, gun.mechanics.kind() == GunItem.Kind.LAS ? 0xFFE8452E : BRASS);
        if (GunClient.reloading()) {
            float p = GunClient.reloadProgress(mc, gun);
            g.fill(bx, by, bx + Math.round(bw * p), by + 2, GREEN);
            g.drawString(font, net.minecraft.network.chat.Component.translatable("gui.warpbound.gun.reloading"), x, y - 11, GREEN, true);
        } else if (shown == 0 && mags > 0) {
            g.drawString(font, net.minecraft.network.chat.Component.translatable("gui.warpbound.gun.press_reload", GunClient.RELOAD.getTranslatedKeyMessage()), x, y - 11, 0xFFE8B84A, true);
        } else if (shown == 0) {
            g.drawString(font, net.minecraft.network.chat.Component.translatable("gui.warpbound.gun.no_ammo"), x, y - 11, RED, true);
        }
    }
}
