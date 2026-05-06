package infrastructure

import future.keywords.if
import future.keywords.in

# Default deny — must explicitly pass all checks
default allow = false

# Allow only when there are zero violations
allow if {
    count(violations) == 0
}

# Collect all violations into a set
violations contains msg if {
    input.disk_free_gb < data.thresholds.min_disk_free_gb
    msg := sprintf(
        "Disk free (%.1f GB) is below minimum (%.1f GB)",
        [input.disk_free_gb, data.thresholds.min_disk_free_gb]
    )
}

violations contains msg if {
    input.cpu_load > data.thresholds.max_cpu_load
    msg := sprintf(
        "CPU load (%.2f) exceeds maximum (%.2f)",
        [input.cpu_load, data.thresholds.max_cpu_load]
    )
}
