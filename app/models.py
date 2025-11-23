from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Q
from decimal import Decimal


# ==========================================
#  NUEVO MÓDULO GEOGRÁFICO (Cascada)
# ==========================================

class Pais(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'm_pais'
        verbose_name = 'País'
        verbose_name_plural = 'Países'

    def __str__(self):
        return self.nombre


class Provincia(models.Model):
    """
    Representa una Provincia, Estado o Departamento según el país.
    """
    pais = models.ForeignKey(Pais, on_delete=models.CASCADE, related_name='provincias')
    nombre = models.CharField(max_length=100)

    class Meta:
        db_table = 'm_provincia'
        verbose_name = 'Provincia / Estado'
        unique_together = ('pais', 'nombre')  # No puede haber dos "Guayas" en el mismo País

    def __str__(self):
        return f"{self.nombre} ({self.pais.nombre})"


class Ciudad(models.Model):
    provincia = models.ForeignKey(Provincia, on_delete=models.CASCADE, related_name='ciudades')
    nombre = models.CharField(max_length=100)

    class Meta:
        db_table = 'm_ciudad'
        verbose_name = 'Ciudad'
        unique_together = ('provincia', 'nombre')

    def __str__(self):
        return f"{self.nombre}, {self.provincia.nombre}"


# ==========================================
#  MODIFICACIÓN EN RESTAURANTE
# ==========================================

class Restaurante(models.Model):
    nombre = models.CharField(max_length=100)
    ruc = models.CharField(max_length=13, unique=True)
    sucursal = models.PositiveIntegerField(help_text="Número de sucursal (Ej: 1, 2, 3...)")

    # CAMBIO CRÍTICO: En lugar de textos sueltos, ahora vinculamos a la Ciudad.
    # Al saber la ciudad, automáticamente sabemos la provincia y el país por la relación en cascada.
    ciudad = models.ForeignKey(Ciudad, on_delete=models.PROTECT, verbose_name="Ubicación (Ciudad)")

    ubicacion = models.CharField(max_length=200, help_text="Calle principal, secundaria y número")

    class Meta:
        db_table = 'm_restaurante'
        verbose_name = 'Restaurante / Sucursal'
        unique_together = ('sucursal', 'ruc')

    def __str__(self):
        return f"{self.nombre} - Suc. {self.sucursal} ({self.ciudad.nombre})"


# ... (El resto de modelos Cargo, Empleado, etc. sigue igual) ...


class Cargo(models.Model):
    nombre = models.CharField(max_length=50)
    sueldo = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'm_cargo'

    def __str__(self):
        return self.nombre


class Empleado(models.Model):
    # --- NUEVOS CAMPOS SOLICITADOS ---
    cargo = models.ForeignKey(Cargo, on_delete=models.PROTECT)
    cedula = models.CharField(max_length=10, unique=True, null=True)  # null=True para no romper datos viejos
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100, null=True)
    edad = models.PositiveIntegerField(null=True)
    direccion_domicilio = models.CharField(max_length=255, null=True)
    telefono_fijo = models.CharField(max_length=15, blank=True, null=True)
    celular = models.CharField(max_length=15, null=True)

    class Meta:
        db_table = 'm_empleado'

    def __str__(self):
        return f"{self.nombre} {self.apellido or ''}"


class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=15)

    class Meta:
        db_table = 'm_cliente'

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'm_producto'

    def __str__(self):
        return self.nombre


class TipoReclamo(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True)

    class Meta:
        db_table = 'm_tipo_reclamo'

    def __str__(self):
        return self.nombre


class TipoSolucion(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True)

    class Meta:
        db_table = 'm_tipo_solucion'

    def __str__(self):
        return self.nombre


# ==========================================
#  TABLAS TRANSACCIONALES (T_)
# ==========================================

class Factura(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    empleado = models.ForeignKey(Empleado, on_delete=models.PROTECT)
    restaurante = models.ForeignKey(Restaurante, on_delete=models.PROTECT)

    # LÓGICA: Ambos campos son automáticos (editable=False)
    codigo_factura = models.CharField(max_length=50, unique=True, editable=False)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0, editable=False)

    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 't_factura'

    def save(self, *args, **kwargs):
        # 1. Generación Automática de Código (Como vimos antes)
        if not self.codigo_factura:
            ultima = Factura.objects.all().order_by('id').last()
            nuevo_numero = (ultima.id + 1) if ultima else 1
            self.codigo_factura = f"001-001-{nuevo_numero:09d}"

        super().save(*args, **kwargs)

    def actualizar_total(self):
        """
        Esta función recorre todos los detalles hijos y suma sus valores.
        Se llama automáticamente desde el hijo (DetalleFactura).
        """
        # Sumamos: cantidad * precio para cada detalle en esta factura
        total_calc = sum(d.cantidad * d.precio_unitario for d in self.detalles.all())
        self.total = total_calc
        self.save()  # Guardamos solo la factura para actualizar el total

    def __str__(self):
        return f"Factura #{self.codigo_factura} (${self.total})"




class Reclamo(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_PROCESO', 'En Proceso'),
        ('RESUELTO', 'Resuelto'),
        # ELIMINADO: 'RECHAZADO' ya no existe como estado.
    ]

    factura = models.ForeignKey('Factura', on_delete=models.PROTECT)
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    descripcion_general = models.TextField()

    class Meta:
        db_table = 't_reclamo'

    def __str__(self):
        return f"Reclamo #{self.id} ({self.get_estado_display()})"


class Solucion(models.Model):
    """
    Cabecera de la solución.
    """
    # LOGICA 1: limit_choices_to
    # Solo permite seleccionar reclamos que NO estén resueltos.
    # Esto filtra el dropdown automáticamente en el Admin.
    reclamo = models.OneToOneField(
        Reclamo,
        on_delete=models.PROTECT,
        related_name='solucion_general',
        limit_choices_to=Q(estado__in=['PENDIENTE', 'EN_PROCESO'])
    )
    empleado = models.ForeignKey('Empleado', on_delete=models.PROTECT, help_text="Empleado que cierra el caso")
    fecha_cierre = models.DateTimeField(auto_now_add=True)
    comentario_final = models.TextField(blank=True)

    class Meta:
        db_table = 't_solucion'
        verbose_name = "Solución (Cierre)"

    def save(self, *args, **kwargs):
        """
        LÓGICA 3: AUTOMATIZACIÓN
        Al guardar la solución, actualizamos automáticamente el estado del Reclamo a 'RESUELTO'.
        """
        is_new = self.pk is None  # Verificamos si es una creación nueva
        super().save(*args, **kwargs)  # Guardamos la solución primero

        if is_new:
            self.reclamo.estado = 'RESUELTO'
            self.reclamo.save()

    def __str__(self):
        return f"Solución al Reclamo #{self.reclamo.id}"


# ==========================================
#  TABLAS DE DETALLE (D_)
# ==========================================

class DetalleFactura(models.Model):
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()

    # LÓGICA: El precio se toma del producto, el usuario no lo escribe.
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    class Meta:
        db_table = 'd_detalle_factura'

    def save(self, *args, **kwargs):
        # 1. Antes de guardar, buscamos el precio real del producto
        self.precio_unitario = self.producto.precio

        # 2. Guardamos el detalle (la fila de la hamburguesa)
        super().save(*args, **kwargs)

        # 3. ¡MAGIA! Le decimos al Padre (Factura) que recalcule su total
        self.factura.actualizar_total()

    def delete(self, *args, **kwargs):
        # Si borramos un detalle, también hay que restar del total
        factura_padre = self.factura  # Guardamos la referencia antes de borrar
        super().delete(*args, **kwargs)
        factura_padre.actualizar_total()

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"


class DetalleReclamo(models.Model):
    reclamo = models.ForeignKey(Reclamo, on_delete=models.CASCADE, related_name='detalles_reclamo')
    producto = models.ForeignKey('Producto', on_delete=models.PROTECT)
    tipo_reclamo = models.ForeignKey('TipoReclamo', on_delete=models.PROTECT)
    motivo_especifico = models.TextField()
    evidencia_foto = models.FileField(upload_to='evidencias/', null=True, blank=True, verbose_name="Foto Evidencia")

    class Meta:
        db_table = 'd_detalle_reclamo'

    def clean(self):
        # Validación para asegurar que el producto pertenece a la factura
        if hasattr(self, 'reclamo') and self.reclamo.factura:
            # Nota: Usamos 'Factura' string o importación directa según orden de clases
            # Aquí asumo que DetalleFactura ya está definida arriba o importada
            from .models import DetalleFactura
            existe = DetalleFactura.objects.filter(factura=self.reclamo.factura, producto=self.producto).exists()
            if not existe:
                raise ValidationError(f"El producto '{self.producto.nombre}' no pertenece a la Factura.")

    def __str__(self):
        return f"Detalle: {self.producto.nombre}"

class DetalleSolucion(models.Model):
    solucion_general = models.ForeignKey(Solucion, on_delete=models.CASCADE, related_name='detalles_solucion', null=True)
    detalle_reclamo = models.OneToOneField(DetalleReclamo, on_delete=models.PROTECT)
    tipo_solucion = models.ForeignKey('TipoSolucion', on_delete=models.PROTECT)
    observacion = models.TextField()

    class Meta:
        db_table = 'd_detalle_solucion'

    def __str__(self):
        return f"Resolución para {self.detalle_reclamo.producto.nombre}"