extends Node3D

@export var projectile_scene: PackedScene = preload("res://yoyo_projectile.tscn")
@onready var launch_point: Marker3D = $Marker3D

var is_thrown: bool = false

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("attack") and not is_thrown:
		throw_yoyo()

func throw_yoyo() -> void:
	is_thrown = true
	$blockbench_export.hide() # Hide held mesh while it flies
	
	# Instantiate and setup projectile
	var proj = projectile_scene.instantiate()
	proj.global_transform = launch_point.global_transform
	proj.set_owner_player(self) # Hand over reference so it knows who to return to
	
	# Add to main world scene tree so it moves independently of player movement
	get_tree().current_scene.add_child(proj)

func return_received() -> void:
	is_thrown = false
	$blockbench_export.show() # Make held mesh visible again
