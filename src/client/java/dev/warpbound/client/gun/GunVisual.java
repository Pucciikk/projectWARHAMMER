package dev.warpbound.client.gun;

import dev.warpbound.core.WarpboundItems;
import dev.warpbound.gun.GunItem;
import net.minecraft.world.item.Item;

import java.util.HashMap;
import java.util.Map;

/**
 * Как оружие лежит и бьётся в руках: только ощущения от первого лица, балансных чисел здесь нет.
 * sightZ — высота прицельной линии в модели (константа SIGHT_Z в скрипте Blender); при прицеливании она встаёт ровно в центр экрана.
 */
record GunVisual(String model, float scale, float hipX, float hipY, float hipZ, float aimZ, float sightZ, float fovAim,
                 float kickBack, float kickPitch, float kickRoll, float camUp, float camSide, float flash, boolean casing) {
    private static final Map<Item, GunVisual> ALL = new HashMap<>();

    static GunVisual of(GunItem gun) {
        return ALL.computeIfAbsent(gun, GunVisual::build);
    }

    private static GunVisual build(Item item) {
        if (item == WarpboundItems.LASGUN) {
            return new GunVisual("lasgun_3d", 0.6f, 0.17f, -0.15f, -0.42f, -0.56f, 0.135f, 0.78f, 0.03f, 1.6f, 0.8f, 0.55f, 0.22f, 0.32f, false);
        }
        // болтер тяжелее: отдача больше и глуше, камера уходит заметнее
        return new GunVisual("bolter_3d", 0.62f, 0.19f, -0.17f, -0.46f, -0.6f, 0.178f, 0.82f, 0.065f, 3.8f, 1.8f, 1.5f, 0.45f, 0.5f, true);
    }
}
