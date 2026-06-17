extends CharacterBody3D

const SPEED = 5.0
const JUMP_VELOCITY = 4.5
const ROTATION_SPEED = 20.0 # High value makes it feel snappy like Boomerang Fu

func _ready() -> void:
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

func _physics_process(delta: float) -> void:
	# Add the gravity.
	if not is_on_floor():
		velocity += get_gravity() * delta

	# Handle jump. 
	if Input.is_action_just_pressed("ui_cancel") and is_on_floor():
		velocity.y = JUMP_VELOCITY

	# Get the input direction relative to the WORLD space, not the player's basis
	var input_dir := Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	var direction := Vector3(input_dir.x, 0, input_dir.y).normalized()
	
	if direction:
		velocity.x = direction.x * SPEED
		velocity.z = direction.z * SPEED
		
		# Godot's forward is -Z, so we use direction.x and direction.z accordingly
		var target_angle := atan2(-direction.x, -direction.z)
		
		# Smoothly rotate towards the target angle
		rotation.y = lerp_angle(rotation.y, target_angle, ROTATION_SPEED * delta)
	else:
		velocity.x = move_toward(velocity.x, 0, SPEED)
		velocity.z = move_toward(velocity.z, 0, SPEED)
		
	move_and_slide()
