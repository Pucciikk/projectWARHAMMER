package dev.warpbound.client.player;

import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.player.Player;

import java.util.HashMap;
import java.util.Map;

/**
 * Состояние движения игрока в модели Астартес, по одному на игрока (клиент): сглаженная скорость тела, текущий аллюр,
 * начало последнего взмаха и какой рукой, счётчик попаданий (для стороны вздрагивания).
 */
public final class PlayerMotion {
    public static final class State {
        public float speed;
        public int gait = -1;
        public float swingStart = -1000;
        public boolean swingLeft;
        public int flinches;
        /** Фаза шага и веса смешивания движений. */
        public final dev.warpbound.client.entity.BipedMotion.State motion = new dev.warpbound.client.entity.BipedMotion.State();
        /** Веса действий рук (PlayerActions). */
        public final PlayerActions.State actions = new PlayerActions.State();
        private int speedTick = Integer.MIN_VALUE;
        private int lastSwingTime;
        private boolean wasSwinging;
        private int lastHurt;
    }

    private static final Map<Integer, State> STATES = new HashMap<>();

    private PlayerMotion() {
    }

    public static void clear() {
        STATES.clear();
    }

    /** Обновить и вернуть состояние: раз в тик скорость, каждый кадр — проверка нового взмаха и попадания. */
    public static State update(Player p) {
        State s = STATES.computeIfAbsent(p.getId(), id -> new State());
        if (s.speedTick != p.tickCount) {
            s.speedTick = p.tickCount;
            double dx = p.getX() - p.xo, dz = p.getZ() - p.zo;
            float raw = (float) (Math.sqrt(dx * dx + dz * dz) * 20);
            s.speed += (raw - s.speed) * 0.45f;
        }
        // новый взмах: начался или перезапустился (копание повторяет взмах, не дожидаясь конца)
        if (p.swinging && (!s.wasSwinging || p.swingTime < s.lastSwingTime)) {
            s.swingStart = p.tickCount + Math.max(0, p.swingTime);
            HumanoidArm arm = p.swingingArm == InteractionHand.MAIN_HAND ? p.getMainArm() : p.getMainArm().getOpposite();
            s.swingLeft = arm == HumanoidArm.LEFT;
        }
        s.lastSwingTime = p.swingTime;
        s.wasSwinging = p.swinging;
        if (p.hurtTime > s.lastHurt) s.flinches++;
        s.lastHurt = p.hurtTime;
        return s;
    }
}
