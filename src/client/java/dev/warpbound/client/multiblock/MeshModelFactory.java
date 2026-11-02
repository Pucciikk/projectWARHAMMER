package dev.warpbound.client.multiblock;

import net.minecraft.core.Direction;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;
import org.joml.Vector3f;
import software.bernie.geckolib.cache.object.BakedGeoModel;
import software.bernie.geckolib.cache.object.GeoBone;
import software.bernie.geckolib.cache.object.GeoCube;
import software.bernie.geckolib.cache.object.GeoQuad;
import software.bernie.geckolib.cache.object.GeoVertex;
import software.bernie.geckolib.loading.json.raw.Bone;
import software.bernie.geckolib.loading.json.raw.Cube;
import software.bernie.geckolib.loading.json.raw.ModelProperties;
import software.bernie.geckolib.loading.json.raw.PolyMesh;
import software.bernie.geckolib.loading.object.BakedModelFactory;
import software.bernie.geckolib.loading.object.BoneStructure;
import software.bernie.geckolib.loading.object.GeometryTree;
import software.bernie.geckolib.util.RenderUtil;

import java.util.ArrayList;
import java.util.List;

/**
 * Сборка моделей мода: кубы — как обычно в GeckoLib, плюс настоящая геометрия из Blender ({@code poly_mesh} в кости).
 * <p>
 * Формат меша: {@code positions} — пиксели модели (x как в кубах Bedrock), {@code uvs} — 0..1 от верхнего левого угла,
 * {@code polys} — четырёхугольники [[позиция, нормаль, uv] × 4], у треугольника последняя вершина повторяется.
 * Нормаль грани считаем сами, поэтому грани плоские, как и задумано для техники.
 */
public final class MeshModelFactory implements BakedModelFactory {
    static final double MESH_PLAIN = -1, MESH_GLOW = -2;

    @Override
    public BakedGeoModel constructGeoModel(GeometryTree tree) {
        List<GeoBone> bones = new ArrayList<>();
        for (BoneStructure bone : tree.topLevelBones().values()) {
            bones.add(constructBone(bone, tree.properties(), null));
        }
        return new BakedGeoModel(bones, tree.properties());
    }

    @Override
    public GeoBone constructBone(BoneStructure structure, ModelProperties properties, @Nullable GeoBone parent) {
        Bone raw = structure.self();
        GeoBone bone = new GeoBone(parent, raw.name(), raw.mirror(), raw.inflate(), raw.neverRender(), raw.reset());
        Vec3 rotation = RenderUtil.arrayToVec(raw.rotation());
        Vec3 pivot = RenderUtil.arrayToVec(raw.pivot());
        bone.updateRotation((float) Math.toRadians(-rotation.x), (float) Math.toRadians(-rotation.y), (float) Math.toRadians(rotation.z));
        bone.updatePivot((float) -pivot.x, (float) pivot.y, (float) pivot.z);

        for (Cube cube : raw.cubes()) {
            bone.getCubes().add(constructCube(cube, properties, bone));
        }
        if (raw.polyMesh() != null) {
            addMesh(bone, raw.polyMesh());
        }
        for (BoneStructure child : structure.children().values()) {
            bone.getChildBones().add(constructBone(child, properties, bone));
        }
        return bone;
    }

    @Override
    public GeoCube constructCube(Cube cube, ModelProperties properties, GeoBone bone) {
        return BakedModelFactory.DEFAULT_FACTORY.constructCube(cube, properties, bone);
    }

    /** Меш кости — «кубы» с произвольными четырёхугольниками: обычные грани и светящиеся отдельно. */
    private static void addMesh(GeoBone bone, PolyMesh mesh) {
        double[] pos = mesh.positions();
        double[] uv = mesh.uvs();
        double[][][] polys = mesh.polysUnion().union();
        List<GeoQuad> plain = new ArrayList<>(polys.length);
        List<GeoQuad> glowing = new ArrayList<>();
        for (int i = 0; i < polys.length; i++) {
            GeoVertex[] vertices = new GeoVertex[4];
            for (int v = 0; v < 4; v++) {
                int p = (int) polys[i][v][0] * 3;
                int t = (int) polys[i][v][2] * 2;
                vertices[v] = new GeoVertex(new Vector3f((float) (-pos[p] / 16), (float) (pos[p + 1] / 16), (float) (pos[p + 2] / 16)),
                        (float) uv[t], (float) uv[t + 1]);
            }
            (polys[i][0][1] > 0 ? glowing : plain).add(new GeoQuad(vertices, normal(vertices), Direction.NORTH));
        }
        // размер отрицательный — пометка для MachineRenderer: у настоящих кубов он не бывает меньше нуля
        bone.getCubes().add(cube(plain, MESH_PLAIN));
        if (!glowing.isEmpty()) bone.getCubes().add(cube(glowing, MESH_GLOW));
    }

    private static GeoCube cube(List<GeoQuad> quads, double mark) {
        return new GeoCube(quads.toArray(new GeoQuad[0]), Vec3.ZERO, Vec3.ZERO, new Vec3(mark, 1, 1), 0, false);
    }

    private static Vector3f normal(GeoVertex[] v) {
        Vector3f a = new Vector3f(v[1].position()).sub(v[0].position());
        Vector3f b = new Vector3f(v[2].position()).sub(v[0].position());
        Vector3f n = a.cross(b);
        return n.lengthSquared() > 1e-12f ? n.normalize() : new Vector3f(0, 1, 0);
    }
}
