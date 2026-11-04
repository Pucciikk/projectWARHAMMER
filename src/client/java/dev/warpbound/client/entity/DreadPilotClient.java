package dev.warpbound.client.entity;

import com.mojang.blaze3d.platform.InputConstants;
import dev.warpbound.entity.dreadnought.concept.DreadConceptEntity;
import net.fabricmc.fabric.api.client.keybinding.v1.KeyBindingHelper;
import net.minecraft.client.KeyMapping;
import org.lwjgl.glfw.GLFW;
import dev.warpbound.network.DreadControlPayload;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.fabricmc.fabric.api.event.client.player.ClientPreAttackCallback;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;

/**
 * Управление дредноутом на клиенте: ЛКМ стреляет, пока зажата, ПКМ бьёт клешнёй, V толкает. Ванильные удар и использование предмета за пилота не срабатывают.
 * Команды autoFire и autoClaw — для сценариев автотеста.
 */
public final class DreadPilotClient {
    public static final KeyMapping SHOVE = KeyBindingHelper.registerKeyBinding(new KeyMapping("key.warpbound.dread_shove", InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_V, "key.categories.warpbound"));
    private static boolean autoFire;

    private DreadPilotClient() {
    }

    public static boolean piloting(LocalPlayer player) {
        return player != null && player.getVehicle() instanceof DreadConceptEntity;
    }

    public static void register() {
        ClientPreAttackCallback.EVENT.register((client, player, clicks) -> piloting(player));
        // до обработки кнопок игрой: нажатие забираем себе
        ClientTickEvents.START_CLIENT_TICK.register(DreadPilotClient::tick);
        DreadConceptEntity.stepShake = DreadnoughtFx::kick;
        DreadCockpitHud.register();
    }

    private static void tick(Minecraft mc) {
        LocalPlayer player = mc.player;
        if (!piloting(player)) return;
        if (mc.screen != null) return;
        while (SHOVE.consumeClick()) ClientPlayNetworking.send(new DreadControlPayload(DreadControlPayload.SHOVE));
        boolean claw = false;
        while (mc.options.keyUse.consumeClick()) claw = true;
        while (mc.options.keyAttack.consumeClick()) {
            ClientPlayNetworking.send(new DreadControlPayload(DreadControlPayload.FIRE));
        }
        if (claw) ClientPlayNetworking.send(new DreadControlPayload(DreadControlPayload.CLAW));
        if (mc.options.keyAttack.isDown() || autoFire) ClientPlayNetworking.send(new DreadControlPayload(DreadControlPayload.FIRE));
    }

    /** Команды сценария автотеста: fire on|off, claw. */
    public static void autotest(String arg) {
        String[] parts = arg.trim().split("\\s+");
        switch (parts[0]) {
            case "fire" -> autoFire = parts.length > 1 && parts[1].equals("on");
            case "claw" -> ClientPlayNetworking.send(new DreadControlPayload(DreadControlPayload.CLAW));
            case "shove" -> ClientPlayNetworking.send(new DreadControlPayload(DreadControlPayload.SHOVE));
            default -> throw new IllegalArgumentException(arg);
        }
    }
}
