#version 150

// Полноэкранный прямоугольник: вершины уже в координатах экрана (-1..1)
in vec3 Position;

out vec2 vNdc;

void main() {
    gl_Position = vec4(Position.xy, 0.0, 1.0);
    vNdc = Position.xy;
}
