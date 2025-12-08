#!/usr/bin/env python3
"""Quick check to visualize the waveform logic"""

import numpy as np
import matplotlib.pyplot as plt

def simulate_triangle(num_samples=1000):
    """Simulate the triangle generator logic"""
    phase_incr = 2**32 // 100  # About 100 samples per period
    phase = 0
    output = []

    for _ in range(num_samples):
        # Extract bit 31 (sign bit of phase)
        msb = (phase >> 31) & 1
        # Extract lower 31 bits
        lower_bits = phase & 0x7FFFFFFF

        if msb == 0:
            # First half: rising
            # Shift phase left by 1 to use full 32-bit range
            triangle = (lower_bits << 1)
            # Convert to signed 32-bit
            if triangle >= 2**31:
                triangle = triangle - 2**32
        else:
            # Second half: falling (invert to create down-slope)
            inverted = (~lower_bits) & 0x7FFFFFFF
            triangle = (inverted << 1)
            # Convert to signed 32-bit
            if triangle >= 2**31:
                triangle = triangle - 2**32

        output.append(triangle)
        phase = (phase + phase_incr) & 0xFFFFFFFF

    return output

def simulate_sine_quadrant(num_samples=1000):
    """Simulate sine with quarter-wave symmetry"""
    phase_incr = 2**32 // 100  # About 100 samples per period
    phase = 0
    output = []

    for _ in range(num_samples):
        # Top 10 bits for LUT (like in the actual design)
        phase_10bit = (phase >> 22) & 0x3FF
        quadrant = (phase_10bit >> 8) & 0x3
        quarter_phase = phase_10bit & 0xFF

        # If in quadrant 1 or 3, mirror the phase
        if quadrant & 1:
            quarter_phase = 255 - quarter_phase

        # Generate sine value (0 to max) for quarter wave
        # Using actual sine for simulation
        angle = (quarter_phase / 256.0) * (np.pi / 2)
        quarter_amp = int(np.sin(angle) * 2147483647)

        # If in quadrants 2 or 3 (second half), negate
        if quadrant & 2:
            sine_out = -quarter_amp
        else:
            sine_out = quarter_amp

        output.append(sine_out)
        phase = (phase + phase_incr) & 0xFFFFFFFF

    return output

# Generate waveforms
triangle = simulate_triangle(400)
sine = simulate_sine_quadrant(400)

# Plot
fig, axes = plt.subplots(2, 1, figsize=(12, 8))

axes[0].plot(triangle)
axes[0].set_title('Simulated Triangle Wave')
axes[0].set_ylabel('Amplitude')
axes[0].grid(True)
axes[0].axhline(y=0, color='r', linestyle='--', alpha=0.3)

axes[1].plot(sine)
axes[1].set_title('Simulated Sine Wave (with Quarter-Wave Symmetry)')
axes[1].set_ylabel('Amplitude')
axes[1].set_xlabel('Sample')
axes[1].grid(True)
axes[1].axhline(y=0, color='r', linestyle='--', alpha=0.3)

plt.tight_layout()
plt.savefig('waveform_simulation.png')
print("Saved waveform_simulation.png")

# Print some diagnostics
print(f"\nTriangle wave:")
print(f"  Min: {min(triangle)}")
print(f"  Max: {max(triangle)}")
print(f"  Range: {max(triangle) - min(triangle)}")

print(f"\nSine wave:")
print(f"  Min: {min(sine)}")
print(f"  Max: {max(sine)}")
print(f"  Range: {max(sine) - min(sine)}")
