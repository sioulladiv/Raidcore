# Game Fixes Applied

## Issues Fixed:

### 1. Speed Issues
- **Player Speed**: Reduced from 3.5 to 2.0
- **Enemy Speed**: Reduced by 50% (multiplied by 0.5) 
- **Reason**: The velocity-based movement system was making characters move too fast

### 2. Wall Collision Layer Issues  
- **Fixed layer names**: Updated to handle "wall lining" and "wall lining 2" (with space)
- **Added fallback options**: Multiple layer name combinations tried
- **Fixed pathfinding**: Updated collision grid to use correct layer data access
- **Added debug output**: Shows which layers are successfully loaded

### 3. Enemy Pathfinding/Movement Issues
- **Minimum attack distance**: Enemies stop moving when within 20 pixels of player
- **Reduced pushback**: When attacking player, enemies only get 50% pushback instead of full stop
- **Velocity preservation**: Enemies maintain 30% velocity after attack instead of complete stop
- **Reason**: Enemies were getting stuck after attacking because velocity was zeroed

### 4. Layer Data Access Fix
- **Fixed array indexing**: Changed from `layer.data[y][x]` to `layer.data[y * width + x]`
- **Reason**: TMX layer data is stored as a flat array, not 2D array

## Files Modified:
1. `entities/player.py` - Reduced player speed
2. `entities/enemy.py` - Reduced enemy speed, fixed attack behavior
3. `game.py` - Fixed collision layer loading, added debug output, fixed pathfinding

## Testing Suggestions:
1. Run the game and check console output for layer loading messages
2. Test wall collisions to ensure both wall layers work
3. Observe enemy behavior - they should approach but stop at attack range
4. Check movement speeds feel appropriate

## Next Steps if Issues Persist:
1. If walls still don't work: Check TMX file layer names directly
2. If enemies too slow/fast: Adjust the 0.5 multiplier in enemy.py
3. If player too slow/fast: Adjust speed value in player.py
4. If pathfinding broken: Check collision grid generation debug output
