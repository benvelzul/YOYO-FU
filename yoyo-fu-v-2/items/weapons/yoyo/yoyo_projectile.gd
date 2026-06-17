extends Area3D

enum State { LAUNCH, HOVER, RETURN }
var current_state: State = State.LAUNCH

@export var max_range_time: float = 0.4
@export var hover_time: float = 0.15
@export var launch_speed: float = 25.0
@export var return_speed: float = 30.0
@export var spin_speed: float = 15.0
@export var damage: int = 1

@onready var visuals: Node3D = $Visuals
@onready var timer: Timer = $StateTimer

var player_source: Node3D = null
var launch_direction: Vector3 = Vector3.FORWARD

func _ready() -> void:
	# Connect collision hit signals
	body_entered.connect(_on_body_entered)
	
	# Initialise flight path direction from spawn angle
	launch_direction = -global_transform.basis.z.normalized() 
	
	# Start forward phase sequence
	timer.start(max_range_time)
	timer.timeout.connect(_on_timer_timeout)

func set_owner_player(player_node: Node3D) -> void:
	player_source = player_node

func _physics_process(delta: float) -> void:
	# Visual Spin effect
	visuals.rotate_y(spin_speed * delta)
	
	# Behavior State Machine
	match current_state:
		State.LAUNCH:
			global_position += launch_direction * launch_speed * delta
			
		State.HOVER:
			# Stay stationary or drift slightly
			pass
			
		State.RETURN:
			if is_instance_valid(player_source):
				var target_pos = player_source.global_position
				var to_player = target_pos - global_position
				
				# Check if arrived back at player
				if to_player.length() < 0.8:
					catch_yoyo()
					return
					
				# Actively track moving player
				global_position += to_player.normalized() * return_speed * delta
			else:
				queue_free() # Clean up if player died

func _on_timer_timeout() -> void:
	# Disconnect timer to reuse safely
	timer.timeout.disconnect(_on_timer_timeout)
	
	if current_state == State.LAUNCH:
		current_state = State.HOVER
		timer.start(hover_time)
		timer.timeout.connect(_on_timer_timeout)
	elif current_state == State.HOVER:
		current_state = State.RETURN

func _on_body_entered(body: Node3D) -> void:
	if body.is_in_group("enemies") and body.has_method("take_damage"):
		body.take_damage(damage)

func catch_yoyo() -> void:
	if is_instance_valid(player_source):
		player_source.return_received()
	queue_free()
