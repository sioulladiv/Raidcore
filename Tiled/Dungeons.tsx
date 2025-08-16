<?xml version="1.0" encoding="UTF-8"?>
<tileset version="1.10" tiledversion="1.11.2" name="Dungeons" tilewidth="16" tileheight="16" tilecount="1024" columns="32">
 <image source="../Dungeon/0x72_DungeonTilesetII_v1.7.png" width="512" height="512"/>
 <tile id="388">
  <animation>
   <frame tileid="388" duration="100"/>
   <frame tileid="387" duration="100"/>
   <frame tileid="386" duration="100"/>
   <frame tileid="385" duration="100"/>
  </animation>
 </tile>
 <tile id="422">
  <animation>
   <frame tileid="419" duration="100"/>
   <frame tileid="417" duration="100"/>
  </animation>
 </tile>
 <wangsets>
  <wangset name="wall" type="mixed" tile="-1">
   <wangcolor name="" color="#ff0000" tile="-1" probability="1"/>
   <wangtile tileid="33" wangid="0,0,0,0,0,1,1,1"/>
   <wangtile tileid="34" wangid="1,0,0,0,1,0,0,0"/>
   <wangtile tileid="35" wangid="0,1,1,1,0,0,0,0"/>
  </wangset>
 </wangsets>
</tileset>
