#version 150

// Небо варпа. Порт браузерного прототипа (warp-prototype/warp-sky.html).
// Координата p строится из направления взгляда: центр «туннеля» — нос корабля (+Z).

uniform mat4 InvViewProj;
uniform float uTime;   // секунды, по модулю 600
uniform float uField;  // Поле Геллера 0..1
uniform float uStorm;  // шторм 0..1
uniform float uCorr;   // порча игрока 0..1
uniform float uEnter;  // 0 = обычный космос, 1 = варп
uniform float uFlash;  // вспышка молнии 0..1
uniform float uSpeed;  // скорость прокрутки туннеля
uniform float uBoltSeed; // форма большой молнии
uniform float uCruise;  // ход корабля на двигателях 0..1: звёзды текут от носа к корме
uniform float uPlanet;  // планета под кораблём 0..1 (1 — на низкой орбите, 0 — ушла)
uniform vec3 uPlanetColor;

in vec2 vNdc;
out vec4 fragColor;

float hash(vec2 p) {
  p = fract(p * vec2(123.34, 456.21));
  p += dot(p, p + 45.32);
  return fract(p.x * p.y);
}

// Шум, периодичный по x: иначе на стыке угла atan() будет шов
float pnoise(vec2 p, float per) {
  vec2 i = floor(p), f = fract(p);
  vec2 u = f * f * (3.0 - 2.0 * f);
  float x0 = mod(i.x, per), x1 = mod(i.x + 1.0, per);
  float a = hash(vec2(x0, i.y)), b = hash(vec2(x1, i.y));
  float c = hash(vec2(x0, i.y + 1.0)), d = hash(vec2(x1, i.y + 1.0));
  return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

float fbm(vec2 p, float per) {
  float v = 0.0, a = 0.5;
  for (int i = 0; i < 5; i++) {
    v += a * pnoise(p, per);
    p *= 2.0; per *= 2.0; a *= 0.5;
  }
  return v;
}

vec3 space(vec2 p, float r, float a) {
  // Звёзды в полярной сетке: при входе в варп вытягиваются в лучи
  float per = 90.0;
  vec2 g = vec2(a / 6.2831853 * per, log(r + 0.001) * 14.0 - uTime * (6.0 * uEnter * uEnter + 2.2 * uCruise));
  vec2 id = floor(g); vec2 f = fract(g) - 0.5;
  id.x = mod(id.x, per);
  float h = hash(id);
  vec2 off = (vec2(hash(id + 3.1), hash(id + 7.7)) - 0.5) * 0.6;
  vec2 d = f - off;
  d.y /= 1.0 + uEnter * 30.0 + uCruise * 5.0;
  float star = smoothstep(0.09, 0.0, length(d)) * step(0.88, h);
  star *= smoothstep(0.02, 0.25, r);
  vec3 col = vec3(0.004, 0.004, 0.012) + vec3(0.9, 0.92, 1.0) * star * (0.5 + 0.5 * hash(id + 1.3));
  col += vec3(0.05, 0.02, 0.08) * fbm(p * 2.0 + 10.0, 1000.0);
  return col;
}

// Ломаный шум для молний: линейная интерполяция даёт острые изломы
float lnoise(float x, float seed) {
  float i = floor(x), f = fract(x);
  return mix(hash(vec2(i, seed)), hash(vec2(i + 1.0, seed)), f);
}

float bdisp(float t, float seed) {
  return (lnoise(t * 5.0, seed) - 0.5) * 0.30
       + (lnoise(t * 17.0, seed + 3.0) - 0.5) * 0.10
       + (lnoise(t * 53.0, seed + 7.0) - 0.5) * 0.035;
}

// Один разряд от a к b: x = белое ядро, y = розовое свечение
vec2 boltSeg(vec2 p, vec2 a, vec2 b, float seed, float w) {
  vec2 ab = b - a;
  float L = length(ab);
  vec2 dir = ab / L;
  vec2 nrm = vec2(-dir.y, dir.x);
  vec2 ap = p - a;
  float t = dot(ap, dir) / L;
  if (t < -0.05 || t > 1.05) return vec2(0.0);
  float tc = clamp(t, 0.0, 1.0);
  float disp = bdisp(tc, seed) * L * sin(tc * 3.14159);
  float dd = abs(dot(ap, nrm) - disp) + max(0.0, abs(t - tc)) * L;
  float taper = mix(1.0, 0.35, tc);
  float core = exp(-dd / (w * taper));
  float glow = 0.012 / (dd + 0.012) * taper;
  return vec2(core, glow * glow);
}

// Разряд с двумя ветками
vec2 bolt(vec2 p, vec2 a, vec2 b, float seed, float w) {
  vec2 g = boltSeg(p, a, b, seed, w);
  vec2 ab = b - a; float L = length(ab); vec2 dir = ab / L; vec2 nrm = vec2(-dir.y, dir.x);
  for (int k = 0; k < 2; k++) {
    float fk = float(k);
    float tb = 0.25 + 0.35 * hash(vec2(seed, fk + 1.0));
    vec2 base = a + ab * tb + nrm * bdisp(tb, seed) * L * sin(tb * 3.14159);
    float side = fk < 0.5 ? 1.0 : -1.0;
    float ang = (0.45 + 0.4 * hash(vec2(seed, fk + 5.0))) * side;
    vec2 bd = vec2(dir.x * cos(ang) - dir.y * sin(ang), dir.x * sin(ang) + dir.y * cos(ang));
    g += boltSeg(p, base, base + bd * L * (0.3 + 0.25 * hash(vec2(seed, fk + 9.0))), seed + 17.0 + fk, w * 0.6) * 0.75;
  }
  return g;
}

// Все молнии кадра: фоновые сами по себе + большой удар по вспышке
vec3 lightning(vec2 p, out float lit) {
  vec3 acc = vec3(0.0);
  lit = 0.0;
  for (int i = 0; i < 4; i++) {
    float fi = float(i);
    float rate = 0.5 + 1.6 * uStorm;
    float cyc = uTime * rate + fi * 2.37;
    float s = floor(cyc), ph = fract(cyc);
    float prob = 0.15 + 0.55 * uStorm + 0.3 * (1.0 - uField);
    float on = step(hash(vec2(s, fi)), prob);
    float life = smoothstep(0.0, 0.02, ph) * exp(-ph * 7.0);
    life *= 0.55 + 0.45 * step(0.4, hash(vec2(floor(uTime * 24.0), fi + s)));
    if (on * life < 0.01) continue;
    vec2 a = vec2(hash(vec2(s, fi + 1.0)) * 2.0 - 1.0, hash(vec2(s, fi + 2.0)) * 0.5 + 0.05);
    float ang = -1.57 + (hash(vec2(s, fi + 3.0)) - 0.5) * 1.8;
    vec2 b = a + vec2(cos(ang), sin(ang)) * (0.45 + 0.45 * hash(vec2(s, fi + 4.0)));
    vec2 g = bolt(p, a, b, s * 13.0 + fi, 0.0036);
    acc += (g.x * vec3(1.0, 0.95, 1.0) + g.y * vec3(1.0, 0.3, 0.6)) * on * life;
    lit += g.y * on * life;
  }
  if (uFlash > 0.01) {
    vec2 a = vec2(hash(vec2(uBoltSeed, 1.0)) * 1.2 - 0.6, 0.5);
    vec2 b = vec2(a.x + (hash(vec2(uBoltSeed, 2.0)) - 0.5) * 0.9, -0.5);
    vec2 g = bolt(p, a, b, uBoltSeed, 0.0055);
    acc += (g.x * vec3(1.0) + g.y * vec3(1.0, 0.35, 0.65)) * uFlash * 1.5;
    lit += g.y * uFlash * 1.5;
  }
  return acc;
}

vec3 warp(vec2 p, float r, float a) {
  float t = uTime;
  float per = 8.0;
  // Туннель: даёт движение вперёд
  float depth = 0.5 / (r + 0.18);
  vec2 tp = vec2(a / 6.2831853 * per + t * 0.06 * (0.5 + uStorm), depth + t * uSpeed * 0.6);
  tp.x += depth * 0.5 * (0.3 + uStorm);
  vec2 q = vec2(fbm(tp + vec2(0.0, t * 0.1), per), fbm(tp + vec2(3.1, 1.7) - vec2(0.0, t * 0.13), per));
  float n = fbm(tp + (1.5 + 2.5 * uStorm) * q, per);

  // Клубящиеся облака в экранных координатах, с подсветкой краёв
  vec2 sp = p * 1.7 + vec2(t * 0.035, t * 0.02) * (1.0 + uStorm);
  vec2 sq = vec2(fbm(sp, 1000.0), fbm(sp + vec2(5.2, 1.3), 1000.0));
  vec2 cp = sp + (1.6 + 1.2 * uStorm) * sq + vec2(0.0, t * 0.05);
  float c = fbm(cp, 1000.0);
  float cl = fbm(cp + vec2(0.035, 0.05), 1000.0);
  float shade = clamp((c - cl) * 9.0 + 0.5, 0.0, 1.0);
  float dens = mix(c, n, 0.4);

  // Палитра: чёрно-багровые провалы, кровь, малиновый, раскалённые блики
  vec3 col = vec3(0.025, 0.0, 0.012);
  col = mix(col, vec3(0.30, 0.015, 0.06), smoothstep(0.30, 0.48, dens));
  col = mix(col, vec3(0.78, 0.05, 0.20), smoothstep(0.44, 0.64, dens));
  col = mix(col, vec3(1.0, 0.28, 0.48), smoothstep(0.60, 0.80, dens) * shade);
  col += vec3(1.0, 0.5, 0.2) * pow(smoothstep(0.68, 0.9, dens), 2.0) * shade * 0.7;
  col += vec3(0.28, 0.03, 0.32) * smoothstep(0.5, 0.25, dens) * smoothstep(0.3, 0.7, sq.x) * 0.7;
  col *= 0.55 + 0.9 * shade;
  // Порча подмешивает ядовитую зелень
  col = mix(col, col.grb * vec3(0.7, 1.3, 0.5), uCorr * 0.45 * smoothstep(0.55, 0.85, q.y));

  // Тонкие багровые жилы
  float ridge = 1.0 - abs(2.0 * fbm(tp * 2.0 + q * 2.0, per * 2.0) - 1.0);
  col += pow(ridge, 10.0) * vec3(1.0, 0.15, 0.25) * (0.25 + 0.4 * uStorm);

  // Тени демонов с глазами: чем слабее Поле, тем их больше
  vec2 cell = tp * 0.5;
  vec2 cid = floor(cell); cid.x = mod(cid.x, per * 0.5);
  vec2 cf = fract(cell) - 0.5;
  float present = step(1.0 - (1.0 - uField) * 0.5, hash(cid + 11.0));
  float band = smoothstep(0.55, 0.9, depth) * smoothstep(2.6, 1.8, depth);
  float body = smoothstep(0.45, 0.12, length(cf * vec2(1.0, 1.25)));
  col *= 1.0 - body * present * band * 0.92;
  float blink = step(0.25, sin(t * (1.0 + hash(cid)) + hash(cid) * 6.28));
  float eyes = smoothstep(0.06, 0.0, length(cf - vec2(0.1, -0.05))) + smoothstep(0.06, 0.0, length(cf - vec2(-0.1, -0.05)));
  col += vec3(1.0, 0.7, 0.15) * eyes * present * band * blink * 2.5;

  // Молнии и подсветка облаков от них
  float lit;
  vec3 bolts = lightning(p, lit);
  col += vec3(1.0, 0.25, 0.45) * lit * dens * 1.2;
  col += bolts;

  // Око туннеля
  col += vec3(1.0, 0.35, 0.45) * 0.012 / (r + 0.08);
  return col;
}

// Планета под кораблём: шар с терминатором, облаками и голубой каймой атмосферы
vec3 planet(vec2 p, vec3 col) {
  if (uPlanet < 0.01) return col;
  vec2 c = vec2(0.0, -0.95);
  float R = 0.75 * uPlanet;
  vec2 q = (p - c) / R;
  float d = length(q);
  float glowRim = smoothstep(1.12, 1.0, d) * smoothstep(0.9, 1.0, d);
  if (d < 1.0) {
    float z = sqrt(1.0 - d * d);
    vec3 n = vec3(q, z);
    float light = clamp(dot(n, normalize(vec3(-0.6, 0.5, 0.6))), 0.0, 1.0);
    float clouds = smoothstep(0.55, 0.75, fbm(q * 3.0 + vec2(uTime * 0.004, 0.0), 1000.0));
    vec3 surf = mix(uPlanetColor * (0.6 + 0.6 * fbm(q * 5.0, 1000.0)), vec3(0.9), clouds * 0.7);
    col = surf * (0.06 + 0.94 * light);
  }
  col += vec3(0.35, 0.6, 1.0) * glowRim * 0.8;
  return col;
}

vec3 scene(vec2 p) {
  float r = length(p);
  float a = atan(p.y, p.x);
  vec3 col = planet(p, space(p, r, a));
  if (uEnter > 0.001) {
    // Разрыв пространства раскрывается из центра рваным краем
    float edge = uEnter * 1.9;
    float jag = r + (pnoise(vec2(a / 6.2831853 * 12.0, uTime * 0.7), 12.0) - 0.5) * 0.3;
    float mask = 1.0 - smoothstep(edge - 0.08, edge, jag);
    vec3 w = warp(p, r, a);

    // Плёнка Поля Геллера: рябь по краям обзора, дыры при слабом Поле
    float rim = smoothstep(0.45, 1.05, r);
    float ripple = pnoise(vec2(a / 6.2831853 * 24.0, r * 10.0 - uTime * 0.8), 24.0);
    float holes = smoothstep(0.5, 0.75, pnoise(vec2(a / 6.2831853 * 6.0, r * 3.0 + uTime * 0.25), 6.0)) * (1.0 - uField);
    float film = rim * (0.18 + 0.3 * ripple) * uField * (1.0 - holes);
    w += vec3(0.55, 0.75, 1.0) * film;
    w += vec3(0.9, 0.1, 0.45) * holes * rim * 0.6;

    col = mix(col, w, mask);
    float tear = exp(-abs(jag - edge) * 35.0) * (1.0 - step(0.999, uEnter));
    col += vec3(1.0, 0.7, 1.0) * tear * 1.5;
  }
  return col;
}

// Направление взгляда → «экранная» координата прототипа вокруг оси носа
vec2 skyCoord(vec3 dir) {
  float theta = acos(clamp(dir.z, -1.0, 1.0));
  float r = theta / 3.14159265 * 1.6;
  vec2 radial = length(dir.xy) > 1e-5 ? normalize(dir.xy) : vec2(1.0, 0.0);
  return radial * r;
}

void main() {
  vec4 world = InvViewProj * vec4(vNdc, 1.0, 1.0);
  vec3 dir = normalize(world.xyz / world.w);
  vec2 p = skyCoord(dir);
  float r = length(p);
  vec3 col = scene(p);

  // Порча: хроматическая аберрация
  if (uCorr > 0.02) {
    vec2 d = normalize(p + 1e-4) * uCorr * r * 0.02;
    col.r = scene(p + d).r;
    col.b = scene(p - d).b;
  }

  col += vec3(0.7, 0.04, 0.12) * uFlash * 0.3;
  col = 1.0 - exp(-col * 1.7);

  // Виньетка по экрану, которая «дышит» при высокой порче
  float sr = length(vNdc) * 0.75;
  float breathe = 0.5 + 0.5 * sin(uTime * 1.7);
  float vig = smoothstep(1.3, 0.4, sr);
  vig *= 1.0 - uCorr * 0.55 * breathe * smoothstep(0.3, 1.0, sr);
  col *= vig;
  col += (hash(gl_FragCoord.xy + fract(uTime) * 100.0) - 0.5) * 0.03;
  fragColor = vec4(col, 1.0);
}
