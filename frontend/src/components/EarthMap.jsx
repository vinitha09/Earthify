import { useEffect, useRef } from "react";

const textureUrl = "https://assets.science.nasa.gov/content/dam/science/esd/eo/images/bmng/bmng-base/july/world.200407.3x5400x2700.jpg";

const vertexShader = `
attribute vec2 position;
void main() { gl_Position = vec4(position, 0.0, 1.0); }
`;

const fragmentShader = `
precision highp float;
uniform vec2 resolution;
uniform sampler2D earth;
uniform float yaw;
uniform float pitch;
uniform vec3 markerNormal;
uniform float markerActive;
void main() {
  vec2 p = (gl_FragCoord.xy - resolution * 0.5) / (min(resolution.x, resolution.y) * 0.43);
  float r2 = dot(p, p);
  if (r2 > 1.0) { gl_FragColor = vec4(0.0); return; }
  float z = sqrt(1.0 - r2);
  float y = p.y * cos(pitch) - z * sin(pitch);
  float zz = p.y * sin(pitch) + z * cos(pitch);
  float lat = asin(clamp(y, -1.0, 1.0));
  float lon = atan(p.x, zz) + yaw;
  vec2 uv = vec2(fract(0.5 + lon / 6.28318530718), 0.5 - lat / 3.14159265359);
  vec3 source = texture2D(earth, uv).rgb;
  vec3 color = pow(max(source, vec3(0.0)), vec3(0.72));
  vec3 surfaceNormal = normalize(vec3(p.x, y, zz));
  vec3 lightDirection = normalize(vec3(-0.45, 0.35, 0.82));
  float daylight = max(0.0, dot(surfaceNormal, lightDirection));
  color = color * (0.3 + 0.82 * daylight) + vec3(0.012, 0.024, 0.045);
  float atmosphere = pow(1.0 - z, 5.0);
  color = mix(color, vec3(0.12, 0.42, 0.9), atmosphere * 0.48);
  color = min(color, vec3(1.0));
  float markerAlignment = dot(normalize(vec3(p.x, y, zz)), markerNormal);
  if (markerActive > 0.5 && markerAlignment > 0.9990) {
    color = mix(color, vec3(1.0, 0.24, 0.08), smoothstep(0.9990, 0.9998, markerAlignment));
    if (markerAlignment > 0.9998) color = vec3(1.0, 0.42, 0.12);
  }
  float edge = 1.0 - smoothstep(0.985, 1.0, r2);
  gl_FragColor = vec4(color, edge);
}
`;

function shader(gl, type, source) {
  const item = gl.createShader(type);
  gl.shaderSource(item, source);
  gl.compileShader(item);
  if (!gl.getShaderParameter(item, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(item));
  return item;
}

export default function EarthMap({ coordinates, onSelect }) {
  const canvasRef = useRef(null);
  const onSelectRef = useRef(onSelect);
  const coordinatesRef = useRef(coordinates);
  onSelectRef.current = onSelect;
  coordinatesRef.current = coordinates;

  useEffect(() => {
    const canvas = canvasRef.current;
    const gl = canvas.getContext("webgl", { alpha: true, antialias: true });
    if (!gl) return undefined;

    const program = gl.createProgram();
    gl.attachShader(program, shader(gl, gl.VERTEX_SHADER, vertexShader));
    gl.attachShader(program, shader(gl, gl.FRAGMENT_SHADER, fragmentShader));
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) return undefined;
    gl.useProgram(program);

    const buffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1]), gl.STATIC_DRAW);
    const position = gl.getAttribLocation(program, "position");
    gl.enableVertexAttribArray(position);
    gl.vertexAttribPointer(position, 2, gl.FLOAT, false, 0, 0);

    const texture = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, texture);
    // NASA's equirectangular texture is non-power-of-two, so WebGL 1 requires
    // clamped wrapping. Longitude is wrapped in the shader with fract().
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);

    const view = { yaw: 0, pitch: 0, zoom: 1, dragging: false, x: 0, y: 0, moved: false };
    let loaded = false;
    let previousFrame = performance.now();
    let animationFrame;
    const image = new Image();
    image.crossOrigin = "anonymous";
    image.onload = () => {
      gl.bindTexture(gl.TEXTURE_2D, texture);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB, gl.RGB, gl.UNSIGNED_BYTE, image);
      loaded = true;
      draw();
    };
    image.src = textureUrl;

    function draw() {
      const rect = canvas.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const width = Math.max(1, Math.round(rect.width * dpr));
      const height = Math.max(1, Math.round(rect.height * dpr));
      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width;
        canvas.height = height;
      }
      gl.viewport(0, 0, width, height);
      gl.clearColor(0, 0, 0, 0);
      gl.clear(gl.COLOR_BUFFER_BIT);
      if (!loaded) return;
      gl.uniform2f(gl.getUniformLocation(program, "resolution"), width, height);
      gl.uniform1f(gl.getUniformLocation(program, "yaw"), view.yaw);
      gl.uniform1f(gl.getUniformLocation(program, "pitch"), view.pitch);
      const marker = coordinatesRef.current;
      if (marker) {
        const lat = marker[0] * Math.PI / 180;
        const lon = marker[1] * Math.PI / 180 - view.yaw;
        const y0 = Math.sin(lat);
        const z0 = Math.cos(lat) * Math.cos(lon);
        // Compare in the same world-space frame used by the fragment shader.
        gl.uniform3f(gl.getUniformLocation(program, "markerNormal"), Math.cos(lat) * Math.sin(lon), y0, z0);
        gl.uniform1f(gl.getUniformLocation(program, "markerActive"), 1);
      } else {
        gl.uniform3f(gl.getUniformLocation(program, "markerNormal"), 0, 0, 1);
        gl.uniform1f(gl.getUniformLocation(program, "markerActive"), 0);
      }
      gl.drawArrays(gl.TRIANGLES, 0, 6);
    }

    function setZoom(zoom) {
      view.zoom = Math.max(0.75, Math.min(1.8, zoom));
      canvas.style.width = `${view.zoom * 100}%`;
      canvas.style.height = `${view.zoom * 100}%`;
      draw();
    }

    function focusLocation([lat, lon]) {
      const longitude = lon * Math.PI / 180;
      view.yaw = longitude + 2 * Math.PI * Math.round((view.yaw - longitude) / (2 * Math.PI));
      view.pitch = -lat * Math.PI / 180;
      setZoom(1.8);
    }

    function pointToLocation(event) {
      const rect = canvas.getBoundingClientRect();
      const radius = Math.min(rect.width, rect.height) * 0.43;
      const x = (event.clientX - rect.left - rect.width / 2) / radius;
      const screenY = (rect.height / 2 - (event.clientY - rect.top)) / radius;
      const r2 = x * x + screenY * screenY;
      if (r2 > 1) return null;
      const z = Math.sqrt(1 - r2);
      // Invert the same pitch transform used to project screen points onto Earth.
      const y = screenY * Math.cos(view.pitch) - z * Math.sin(view.pitch);
      const zz = screenY * Math.sin(view.pitch) + z * Math.cos(view.pitch);
      return [Math.asin(Math.max(-1, Math.min(1, y))) * 180 / Math.PI, ((Math.atan2(x, zz) + view.yaw) * 180 / Math.PI + 540) % 360 - 180];
    }

    function pointerDown(event) {
      if (event.button !== 0) return;
      view.dragging = true;
      view.moved = false;
      view.x = event.clientX;
      view.y = event.clientY;
      canvas.setPointerCapture(event.pointerId);
    }

    function pointerMove(event) {
      if (!view.dragging) return;
      const dx = event.clientX - view.x;
      const dy = event.clientY - view.y;
      if (Math.abs(dx) + Math.abs(dy) > 2) view.moved = true;
      view.yaw -= dx * 0.006 / view.zoom;
      view.pitch = Math.max(-1.35, Math.min(1.35, view.pitch + dy * 0.006 / view.zoom));
      view.x = event.clientX;
      view.y = event.clientY;
      draw();
    }

    function pointerUp(event) {
      if (!view.dragging) return;
      view.dragging = false;
      if (!view.moved) selectPoint(event);
    }

    function selectPoint(event) {
      const location = pointToLocation(event);
      if (!location) return;
      focusLocation(location);
      onSelectRef.current(location);
    }
    function wheel(event) {
      event.preventDefault();
      setZoom(view.zoom + (event.deltaY < 0 ? 0.08 : -0.08));
    }
    function keyDown(event) {
      const step = event.shiftKey ? 0.25 : 0.1;
      if (event.key === "ArrowLeft") view.yaw -= step;
      else if (event.key === "ArrowRight") view.yaw += step;
      else if (event.key === "ArrowUp") view.pitch = Math.max(-1.35, view.pitch - step);
      else if (event.key === "ArrowDown") view.pitch = Math.min(1.35, view.pitch + step);
      else if (event.key === "+" || event.key === "=") setZoom(view.zoom + 0.1);
      else if (event.key === "-") setZoom(view.zoom - 0.1);
      else return;
      event.preventDefault();
      draw();
    }
    function animate(now) {
      const delta = Math.min(0.05, (now - previousFrame) / 1000);
      previousFrame = now;
      if (!view.dragging && !coordinatesRef.current) {
        view.yaw += delta * 0.045;
        draw();
      }
      animationFrame = requestAnimationFrame(animate);
    }
    const observer = new ResizeObserver(draw);
    const updateMarker = () => draw();
    observer.observe(canvas);
    canvas.addEventListener("globe-update", updateMarker);
    canvas.addEventListener("pointerdown", pointerDown);
    canvas.addEventListener("pointermove", pointerMove);
    canvas.addEventListener("pointerup", pointerUp);
    canvas.addEventListener("pointercancel", pointerUp);
    canvas.addEventListener("wheel", wheel, { passive: false });
    canvas.addEventListener("keydown", keyDown);
    draw();
    animationFrame = requestAnimationFrame(animate);
    return () => {
      observer.disconnect();
      cancelAnimationFrame(animationFrame);
      canvas.removeEventListener("globe-update", updateMarker);
      canvas.removeEventListener("pointerdown", pointerDown);
      canvas.removeEventListener("pointermove", pointerMove);
      canvas.removeEventListener("pointerup", pointerUp);
      canvas.removeEventListener("pointercancel", pointerUp);
      canvas.removeEventListener("wheel", wheel);
      canvas.removeEventListener("keydown", keyDown);
      image.onload = null;
      gl.deleteTexture(texture);
      gl.deleteBuffer(buffer);
      gl.deleteProgram(program);
    };
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (canvas) canvas.dispatchEvent(new Event("globe-update"));
  }, [coordinates]);

  return <div className="mapbox globe-box" role="region" aria-label="Interactive 3D globe">
    <canvas ref={canvasRef} className="globe-canvas" tabIndex={0} aria-label="Interactive globe. Drag to rotate, click to select a place, scroll or use plus and minus to zoom." />
  </div>;
}
