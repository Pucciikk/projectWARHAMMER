package dev.warpbound.client.player;

import dev.warpbound.entity.astartes.AstartesConcepts;
import dev.warpbound.network.GeneFormPayload;
import dev.warpbound.player.GeneForm;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.world.entity.player.Player;

import java.util.HashMap;
import java.util.Map;

/** Формы тела игроков, которых видит клиент (номер сущности → форма). Приходят пакетом GeneFormPayload. */
public final class ClientGeneForms {
    private static final Map<Integer, GeneForm> FORMS = new HashMap<>();

    private ClientGeneForms() {
    }

    public static GeneForm get(Player player) {
        return FORMS.getOrDefault(player.getId(), GeneForm.HUMAN);
    }

    /** Аллюры и клипы формы: те же, что у NPC той же модели. */
    public static AstartesConcepts.Variant variant(GeneForm form) {
        return form == GeneForm.THUNDER_WARRIOR ? AstartesConcepts.THUNDER_WARRIOR_VARIANT : AstartesConcepts.ASTARTES_VARIANT;
    }

    public static void register() {
        ClientPlayNetworking.registerGlobalReceiver(GeneFormPayload.TYPE, (payload, context) -> {
            GeneForm form = GeneForm.byId(payload.form());
            if (form == GeneForm.HUMAN) FORMS.remove(payload.entityId());
            else FORMS.put(payload.entityId(), form);
        });
        ClientPlayConnectionEvents.DISCONNECT.register((handler, client) -> {
            FORMS.clear();
            PlayerMotion.clear();
        });
    }
}
