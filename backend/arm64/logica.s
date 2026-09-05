// =====================================================================
// Proyecto: Edificio Inteligente IoT
// Ensamblador AArch64
// =====================================================================

.global _start

.section .data
    file_in:        .asciz "datos.txt"
    file_out:       .asciz "resultado.txt"
    
    // Plantilla de formato de salida obligatorio
    prefix_max:     .ascii "M\xC3\x81X="
    prefix_min:     .ascii "\nMIN="
    prefix_avg:     .ascii "\nAVG="
    prefix_count:   .ascii "\nCOUNT="
    newline:        .ascii "\n"

.section .bss
    .lcomm buffer, 1024         // Buffer de lectura
    .lcomm num_str, 32          // Buffer temporal para conversión de texto

.section .text
_start:
    // --- 1. Inicialización de registros acumuladores ---
    mov x19, #0                 // Máximo absoluto inicial
    mov x20, #9999              // Valor alto inicial para calcular mínimo
    mov x21, #0                 // Suma acumulada
    mov x22, #0                 // Contador (COUNT)
    mov x23, #0                 // Acumulador de dígitos del número actual
    mov x24, #0                 // Bandera indicadora de dígito activo

    // --- 2. Abrir archivo "datos.txt" ---
    mov x0, -100                // AT_FDCWD (Buscar en el directorio actual)
    ldr x1, =file_in
    mov x2, #0                  // O_RDONLY (Solo lectura)
    mov x3, #0
    mov x8, #56                 // Syscall de Linux ARM64: openat
    svc #0
    
    cmp x0, #0
    blt exit_error
    mov x25, x0                 // Guardar File Descriptor de datos.txt

    // --- 3. Leer el contenido de datos.txt ---
    mov x0, x25
    ldr x1, =buffer
    mov x2, #1024
    mov x8, #63                 // Syscall de Linux ARM64: read
    svc #0
    
    cmp x0, #0
    ble close_and_exit
    mov x26, x0                 // Guardar el total de bytes leídos reales
    
    // --- 4. Cerrar archivo datos.txt ---
    mov x0, x25
    mov x8, #57                 // Syscall de Linux ARM64: close
    svc #0

    // --- 5. Procesamiento de la cadena de caracteres ---
    ldr x27, =buffer            // Dirección base del buffer
    mov x28, #0                 // Índice de bytes

parse_loop:
    cmp x28, x26
    bge end_parsing             // Si se alcanzaron todos los bytes, finalizar
    
    ldrb w9, [x27, x28]         // Cargar el byte actual en w9 (Uso seguro)
    add x28, x28, #1
    
    // Validar delimitador '$'[cite: 1]
    cmp w9, #36                 // ASCII '$'
    beq process_last_and_end
    
    // Validar saltos de línea
    cmp w9, #10                 // ASCII '\n'
    beq check_and_save_num
    cmp w9, #13                 // ASCII '\r'
    beq check_and_save_num
    
    // Descartar caracteres no numéricos
    cmp w9, #48
    blt parse_loop
    cmp w9, #57
    bgt parse_loop
    
    // Procesar dígito válido
    sub w9, w9, #48             // Convertir ASCII a entero
    mov x10, #10
    mul x23, x23, x10
    add x23, x23, x9            // Sumar usando x9
    mov x24, #1                 // Bandera activada
    b parse_loop

check_and_save_num:
    cmp x24, #1
    bne parse_loop              
    
    // Máximo
    cmp x23, x19
    ble skip_max
    mov x19, x23
skip_max:
    // Mínimo
    cmp x23, x20
    bge skip_min                
    mov x20, x23
skip_min:
    // Contador y suma
    add x21, x21, x23
    add x22, x22, #1
    
    mov x23, #0
    mov x24, #0
    b parse_loop

process_last_and_end:
    cmp x24, #1
    bne end_parsing
    cmp x23, x19
    ble skip_max2
    mov x19, x23
skip_max2:
    cmp x23, x20
    bge skip_min2               
    mov x20, x23
skip_min2:
    add x21, x21, x23
    add x22, x22, #1

end_parsing:
    // --- 6. Cálculo del Promedio Truncado (AVG) ---
    cmp x22, #0
    beq safe_zero
    udiv x21, x21, x22          // Promedio en ensamblador AArch64[cite: 1]
    b write_results

safe_zero:
    mov x19, #0
    mov x20, #0
    mov x21, #0

    // --- 7. Creación de reporte "resultado.txt" ---
write_results:
    mov x0, -100                // AT_FDCWD
    ldr x1, =file_out
    mov x2, #577                // O_WRONLY | O_CREAT | O_TRUNC
    mov x3, #0644               // Permisos
    mov x8, #56                 // openat
    svc #0
    
    cmp x0, #0
    blt exit_error
    mov x25, x0                 // Guardar FD de resultado.txt

    // Imprimir "MÁX="
    mov x0, x25
    ldr x1, =prefix_max
    mov x2, #5                  // Ajustado a 5 bytes por el caracter especial Á
    mov x8, #64                 
    svc #0
    mov x0, x19
    bl write_int_to_file

    // Imprimir "\nMIN="
    mov x0, x25
    ldr x1, =prefix_min
    mov x2, #5
    mov x8, #64
    svc #0
    mov x0, x20
    bl write_int_to_file

    // Imprimir "\nAVG="
    mov x0, x25
    ldr x1, =prefix_avg
    mov x2, #5
    mov x8, #64
    svc #0
    mov x0, x21
    bl write_int_to_file

    // Imprimir "\nCOUNT="
    mov x0, x25
    ldr x1, =prefix_count
    mov x2, #7
    mov x8, #64
    svc #0
    mov x0, x22
    bl write_int_to_file
    
    // Salto de línea final
    mov x0, x25
    ldr x1, =newline
    mov x2, #1
    mov x8, #64
    svc #0

    // Cerrar archivo
    mov x0, x25
    mov x8, #57                 
    svc #0

close_and_exit:
    mov x0, #0
    mov x8, #93                 // exit
    svc #0

exit_error:
    mov x0, #1
    mov x8, #93
    svc #0

// =====================================================================
// FUNCIÓN: write_int_to_file
// =====================================================================
write_int_to_file:
    stp x29, x30, [sp, #-32]!   
    mov x29, sp
    
    ldr x1, =num_str
    add x1, x1, #30             
    mov x2, #0                  
    mov x3, #10                 

convert_loop:
    udiv x4, x0, x3             
    msub x5, x4, x3, x0         
    add x5, x5, #48             
    sub x1, x1, #1              
    strb w5, [x1]               
    add x2, x2, #1              
    mov x0, x4                  
    cmp x0, #0
    bne convert_loop

    mov x0, x25                 
    mov x8, #64                 // write
    svc #0

    ldp x29, x30, [sp], #32     
    ret
