# OpenRA源码记录

## 输入事件分发

从DefaultInputHandler输入，走不同步行为

![image-20241024002714470](C:\Users\Kamico\AppData\Roaming\Typora\typora-user-images\image-20241024002714470.png)

到Widget的HandleInput进一步分发

然后到Widget的HandleMouseInputOuter层层下发，

比如，下令的右键左键在：WorldInteractionControllerWidget中

>  然后会在OrderManager内，localOrder存储，然后发到服务端，服务端在ProcessOrders中处理，但是我发现都在主线程，可能是有多种方式，我本地跑就在一个线程

比如移动，最后会在Mobile中的ResolveOrder解析



## Actor和ActorInfo

Actor a

a.info

<img src="C:\Users\Kamico\AppData\Roaming\Typora\typora-user-images\image-20241104214859655.png" alt="image-20241104214859655"  />

目前理解是，Actor可以挂Trait，Trait上可以有数据

而ActorInfo上是TraitInfo，是不会改变的，仅用作标识的数据

一个Trait和TraitInfo对应，TraitInfo是只读的

TraitInfo是在Yaml中配置的，相同兵种的同一个Trait的TraitInfo相同

这样拿组件：

```
a.TraitOrDefault<xxx>()
a.Trait<xxx>()
```

这样判有没有组件以及拿Info：

```
a.Info.HasTraitInfo<xxx>()
a.Info.TraitInfo<xxx>() 
```



## Order和Activity

Order是指令，会被解析为Activity

Actor会执行一个(?)Activity，会有Tick

采矿车采矿的指令是：Harvest，target是个wpos
回去储存的指令是：ForceDock，target是harv类型的actor
开始建造是：StartProduction，sub是player
设置集结点是：SetRallyPoint，sub是设置的单位，target还没看
放置建筑是：PlaceBuilding，sub是player，location有值

## Game

Game是全局变量，可以直接获取，里面有渲染相关WorldRenderer，鼠标的CursorManager，音频等等

## 若干位置 CPos MPos WPos PPos

CPos：Cell Pos 整数坐标

WPos：World Pos 一般是CPos 的 X Y 分别乘CellSize（RA是80），不一定是CellSize的整数倍

​	map里有CellContaining可以转成CPos，下面也有转成别的pos的

MPos：Map Pos，在矩形Map时，和CPos是一样的，在等距网格（暂不清楚，斜方形吧）有个转换公式，在MPos里有和CPos互转的接口

PPos：Projected Pos，就是MPos

int2（screenPx）：屏幕像素，WorldRenderer里ProjectedPosition可以把screenPx转成WPos



var mousePos = world.Map.CellContaining(wr.ProjectedPosition(viewport.ViewToWorldPx(Game.Cursor.GetMousePos())));

## 迷雾系统

OpenRA中迷雾有两种，分别叫Fog和Shroud

Fog就是当前点没点亮

Shroud是探没探索过地图

在每个Player下的Shroud中存了信息的，world里也有玩家的相关接口，但world仅处理了玩家，因为是处理渲染用的

## Tick

Actor的Tick在World.cs 中分发，继承了ITick的Actor的Trait会收到Tick

![image-20241109012850986](C:\Users\Kamico\AppData\Roaming\Typora\typora-user-images\image-20241109012850986.png)



Bot的Tick在Bot的ModularBot里分发，继承了IBotTick的Trait会被分配到，Bot本身是一个Player Actor

## Bot相关随笔

INotifyDamage会对Actor通知伤害，在bot这边还会额外来到IBotRespondToAttack

## Map

在map.cs里

![image-20241205001532561](C:\Users\Kamico\AppData\Roaming\Typora\typora-user-images\image-20241205001532561.png)

CellLayer这个数据结构，就是一个N x M的结构，里面存了长宽
