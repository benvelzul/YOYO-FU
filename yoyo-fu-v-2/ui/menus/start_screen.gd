extends Control

func _on_start_btn_pressed() -> void:
	# Replace the path below with the actual file path to your game level scene
	get_tree().change_scene_to_file("res://maps/world.tscn")

func _on_quit_btn_pressed() -> void:
	# This closes the game application entirely
	get_tree().quit()
